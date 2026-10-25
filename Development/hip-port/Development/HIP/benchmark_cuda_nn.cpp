#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <numeric>
#include <fstream>
#include <vector>

namespace hip_reference {
struct LayerBenchmark {
 static void Describe(Network& net) {
   std::printf("GRAPH_STATUS enabled=%u builds=%u replays=%u small=%u wave_owned=%u final_direct=%u\n",unsigned(net.opt.graph),net.graph_builds,net.graph_replays,unsigned(net.small_active),unsigned(net.wave_owned_active),unsigned(net.final_direct_compatible));
   std::printf("COMPACT_VIT contract_w16=%u projection_w16=%u contract_bstream=%u projection_bout=%u inter_byte_calls=%llu\n",unsigned(net.compact_contract_w16),unsigned(net.compact_projection_w16),unsigned(net.compact_contract_bstream_fn!=nullptr),unsigned(net.compact_projection_bout_fn!=nullptr),net.vit_inter_byte_calls);
 }
 static void ValidateGraphInput(Network& net,void* in,void* out,const std::vector<float>& original,const std::vector<float>& reference) {
    auto changed=original;for(size_t i=0;i<changed.size();i++)if(i%4<3)changed[i]=1.f-changed[i];
    net.api.Check(net.api.hipMemcpy(in,changed.data(),changed.size()*4,1),"graph changed input");
    net.Enqueue(in,nullptr,out,0);net.Synchronize();std::vector<float> got(reference.size()),raw(reference.size());
    net.api.Check(net.api.hipMemcpy(got.data(),out,got.size()*4,2),"graph changed read");
    net.EnqueueRaw(in,nullptr,out,0);net.Synchronize();
    net.api.Check(net.api.hipMemcpy(raw.data(),out,raw.size()*4,2),"raw changed read");
    size_t diff=0,changed_values=0;for(size_t i=0;i<got.size();i++){diff+=std::memcmp(&got[i],&raw[i],4)!=0;changed_values+=std::memcmp(&got[i],&reference[i],4)!=0;}
    if(diff||!changed_values)throw std::runtime_error("Graph changed-input mismatch or stale output");
    net.api.Check(net.api.hipMemcpy(in,original.data(),original.size()*4,1),"graph restore input");net.Enqueue(in,nullptr,out,0);net.Synchronize();
    net.api.Check(net.api.hipMemcpy(got.data(),out,got.size()*4,2),"graph restore read");
    size_t restore=0;for(size_t i=0;i<got.size();i++)restore+=std::memcmp(&got[i],&reference[i],4)!=0;
    if(restore)throw std::runtime_error("Graph restore mismatch");
    std::printf("GRAPH_MUTABLE_INPUT raw_bitdiff=%zu changed_values=%zu restored_bitdiff=%zu\n",diff,changed_values,restore);
 }
 static void Run(Network& net, void* in, void* out) {
    net.opt.profile=true;
    net.EnqueueRaw(in,nullptr,out,0); net.Synchronize();
    struct Row { double ms{}; unsigned calls{},block{},grid{}; Handle function{}; };
    std::map<std::string,Row> rows;
    for(auto& t:net.timings) {
      float ms; net.api.Check(net.api.hipEventElapsedTime(&ms,t.begin,t.end),"profile elapsed");
      auto& r=rows[t.name]; r.ms+=ms; ++r.calls; r.block=t.block; r.grid=t.grid; r.function=t.function;
      net.api.hipEventDestroy(t.begin); net.api.hipEventDestroy(t.end);
    }
    net.timings.clear(); net.opt.profile=false;
    auto& drv=hip_probe::detail::Drv();
    // CUDA occupancy API takes the output pointer first.
    using Occ=int(*)(int*,Handle,int,size_t);
    auto occupancy=reinterpret_cast<Occ>(dlsym(dlopen("libcuda.so.1",RTLD_NOW),"cuOccupancyMaxActiveBlocksPerMultiprocessor"));
    double total=0;
    std::printf("Kernel Calls Total_ms Avg_us Grid Block Regs LMem SMem OccW\n");
    for(auto& kv:rows) {
      auto& r=kv.second; Handle fn=r.function;
      int regs=-1,local=-1,shared=-1,blocks=-1;
      if(fn) {drv.cuFuncGetAttribute(&regs,4,fn);drv.cuFuncGetAttribute(&local,3,fn);drv.cuFuncGetAttribute(&shared,1,fn);if(occupancy)occupancy(&blocks,fn,r.block,0);}
      std::printf("%s %u %.6f %.3f %u %u %d %d %d %d\n",kv.first.c_str(),r.calls,r.ms,r.ms*1000/r.calls,r.grid,r.block,regs,local,shared,blocks<0?-1:blocks*((r.block+31)/32));total+=r.ms;
    }
    std::printf("PROFILE_TOTAL %.6f kernels=%zu\n",total,rows.size());
 }
};
}

static hip_reference::Options MakeProductionOptions(unsigned processing_w, unsigned processing_h,
                                                    const std::string& modules, const std::string& assets) {
  hip_reference::Options o;
  o.width = processing_w;
  o.height = processing_h;
  o.post_shift = 3;
  o.fast_vit = true;
  o.wmma = o.wave = o.tiled = o.pooled = true;
  o.graph = false;
  o.modules = modules;
  o.assets = assets;
  o.fast_c32 = o.fused_c32 = o.fused_ffn = o.fast_mh = o.fused_mh = o.mh_wave = o.fast_deep =
      o.fast_prefix = o.packed_weights = o.packed_c32 = o.fp8_normalized = o.fp8_ffn = o.fp8_av =
          o.fp8_deep = o.fp8_middle = o.half_c32 = o.crop_c32 = o.fused_qkv_norm = o.fused_mh_ffn =
              o.tiled_mh_ffn = o.mapped_c32 = o.vit_blocked = o.vit_contract_blocked = true;
  o.tiled_ffn_min_c = 256;
  o.vit_weight_mask = 1;
  o.vit_pack_input = true;
  o.elide_identity_shift = true;
  o.raw_chain = true;
  o.pre_main8 = true;
  o.post_merge_fold = true;
  o.fused_ffn_project = true;
  o.split_ffn_fused = true;
  o.split_mix_blocked = true;
  o.split_project_blocked = true;
  o.vit_qkv_blocked = true;
  o.vit_qkv_fused = true;
  o.mh_project_crop = true;
  o.mh_input_mapped = true;
  o.prefix_fused = true;
  o.direct_prefix_input = true;
  o.grouped_mh_contract = true;
  o.ffn_qkv = true;
  o.ffn_qkv_max_c = 256;
  o.vit_attn_fused = true;
  o.vit_qkv_fp8 = true;
  o.vit_expand_frag = true;
  o.split_mix_h16w = true;
  o.pool_project_h16w = true;
  o.decoder_h16w = true;
  o.c512_qkv_frag = true;
  o.c512_proj_frag = true;
  o.c512_proj_tiles = true;
  o.mh_proj_diag = true;
  o.post_head_fused = true;
  o.c32_finish_fused = true;
  o.down_crop_fused = true;
  o.pool32_h16w = true;
  o.pool_project_group = true;
  o.vit_proj_frag = true;
  o.vit_qkv_frag = true;
  o.vit_contract_frag = true;
  o.prefix_inline = true;
  o.mh_feature_byte = o.mh_proj_diag_fb = o.mh_byte_stream = o.decoder_byte = o.mh_ffn_frag256 = true;
  o.wave_owned = o.c512_m32 = o.vit_proj_n64 = o.pdl = true;
  o.vit_stream = 3;
  o.swin_run = true;
  return o;
}

static uint64_t Fnv1a64(const void* data, size_t len) {
  const uint8_t* p = static_cast<const uint8_t*>(data);
  uint64_t h = 14695981039346656037ull;
  for (size_t i = 0; i < len; ++i) {
    h ^= p[i];
    h *= 1099511628211ull;
  }
  return h;
}

struct CaseConfig {
  const char* label;
  const char* mp_env;
  bool small_geo;
  unsigned w;
  unsigned h;
};

int main(int argc, char** argv) {
  try {
    std::string assets = argc > 1 ? argv[1] : "/home/lmxxf/work/dlss5-assets/native-game-tiled-assets";
    std::string modules = argc > 2 ? argv[2] : "/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/HIP/gfx1201";
    unsigned warmup = argc > 3 ? unsigned(std::stoul(argv[3])) : 10;
    unsigned iters = argc > 4 ? unsigned(std::stoul(argv[4])) : 40;

    setenv("DLSS5_HIP_FAST", "1", 1);
    setenv("DLSS5_FAST_NUMERIC", "1", 1);
    setenv("DLSS5_HIP_WAVE_OWNED", "1", 1);
    setenv("DLSS5_HIP_C512_M32", "1", 1);
    setenv("DLSS5_HIP_VIT_PROJ_N64", "1", 1);
    setenv("DLSS5_HIP_PDL", "1", 1);
    setenv("DLSS5_HIP_VIT_STREAM", "3", 1);
    setenv("DLSS5_HIP_SWIN_RUN", "1", 1);
    setenv("DLSS5_STYLE", "1", 1);
    setenv("DLSS5_VIT_ADAPTIVE", "0", 1);
    setenv("DLSS5_MULTI_PASS_PREDICT", "0", 1);
    setenv("DLSS5_MULTI_PASS_SKIN_PROTECT", "0", 1);

    CaseConfig cases[] = {
        {"0.5x_Small_480p (31-block, 896x512)", "0.5", true, 896, 512},
        {"0.5x_Small_720p (31-block, 1280x768)", "0.5", true, 1280, 768},
        {"0.5x_Small_1080p (31-block, 1920x1152)", "0.5", true, 1920, 1152},
        {"1x_Original_1080p (71-block, 1920x1152)", "1", false, 1920, 1152},
        {"0.5x_Small_900p (31-block, 1600x1024)", "0.5", true, 1600, 1024},
        {"1x_Original_900p (71-block, 1600x960)", "1", false, 1600, 960},
    };

    for (const auto& c : cases) {
      // 720p is an explicit supplemental case; preserve the existing default run list.
      if ((c.w == 1280 || c.w == 896) && !std::getenv("DLSS5_BENCH_WIDTH")) continue;
      if (std::getenv("DLSS5_BENCH_SMALL_ONLY") && !c.small_geo) continue;
      if (const char* width=std::getenv("DLSS5_BENCH_WIDTH");width&&unsigned(std::stoul(width))!=c.w) continue;
      std::printf("\n================================================================\n");
      std::printf("Running Case: %s\n", c.label);
      std::printf("================================================================\n");
      std::fflush(stdout);

      setenv("DLSS5_MULTI_PASS", c.mp_env, 1);
      dlss5_mode::Request(std::strcmp(c.mp_env, "0.5") == 0 ? 0 : 1);

      auto opt = MakeProductionOptions(c.w, c.h, modules, assets);
      opt.small_geometry = c.small_geo;
      opt.graph = std::getenv("DLSS5_BENCH_GRAPH") && std::strcmp(std::getenv("DLSS5_BENCH_GRAPH"),"0") != 0;

      hip_reference::Network net(opt);
      auto& api = net.Runtime();

      const size_t pixels = size_t(c.w) * c.h;
      std::vector<float> host_in(pixels * 4);
      for (unsigned y = 0; y < c.h; ++y) {
        for (unsigned x = 0; x < c.w; ++x) {
          size_t idx = (size_t(y) * c.w + x) * 4;
          host_in[idx + 0] = float((x * 17 + y * 31) % 1024) / 1024.0f;
          host_in[idx + 1] = float((x * 23 + y * 13 + 100) % 1024) / 1024.0f;
          host_in[idx + 2] = float((x * 7 + y * 41 + 200) % 1024) / 1024.0f;
          host_in[idx + 3] = 1.0f;
        }
      }

      void *d_in = nullptr, *d_out = nullptr;
      api.Check(api.hipMalloc(&d_in, pixels * 16), "alloc input");
      api.Check(api.hipMalloc(&d_out, pixels * 12), "alloc output");
      api.Check(api.hipMemcpy(d_in, host_in.data(), pixels * 16, 1), "upload input");

      net.PrepareForExternalInput(false);

      // First frame output capture
      net.Enqueue(d_in, nullptr, d_out, 0);
      net.Synchronize();
      std::vector<float> out_first(pixels * 3, 0.0f);
      api.Check(api.hipMemcpy(out_first.data(), d_out, pixels * 12, 2), "read first output");

      // Warmup
      for (unsigned i = 0; i < warmup; ++i) {
        net.Enqueue(d_in, nullptr, d_out, 0);
      }
      net.Synchronize();

      // Steady-state benchmark
      std::vector<double> wall_ms(iters, 0.0);
      std::vector<float> gpu_ms(iters, 0.0f);
      hip_probe::Handle ev_start = nullptr, ev_stop = nullptr;
      api.Check(api.hipEventCreate(&ev_start), "ev_start");
      api.Check(api.hipEventCreate(&ev_stop), "ev_stop");

      for (unsigned i = 0; i < iters; ++i) {
        auto t0 = std::chrono::steady_clock::now();
        api.Check(api.hipEventRecord(ev_start, net.Stream()), "rec start");
        net.Enqueue(d_in, nullptr, d_out, 0);
        api.Check(api.hipEventRecord(ev_stop, net.Stream()), "rec stop");
        net.Synchronize();
        auto t1 = std::chrono::steady_clock::now();
        wall_ms[i] = std::chrono::duration<double, std::milli>(t1 - t0).count();
        api.Check(api.hipEventElapsedTime(&gpu_ms[i], ev_start, ev_stop), "elapsed");
      }

      std::vector<float> out_last(pixels * 3, 0.0f);
      api.Check(api.hipMemcpy(out_last.data(), d_out, pixels * 12, 2), "read last output");

      if (const char* prefix = std::getenv("DLSS5_BENCH_DUMP")) {
        std::ofstream dump(std::string(prefix)+"-"+std::to_string(c.w)+".rgb32", std::ios::binary);
        dump.write(reinterpret_cast<const char*>(out_last.data()), out_last.size()*4);
      }
      size_t invalid = 0, nonzero = 0, bit_diff = 0;
      double sum = 0.0, min_v = 1e30, max_v = -1e30;
      for (size_t i = 0; i < out_last.size(); ++i) {
        float v = out_last[i];
        if (!std::isfinite(v)) {
          ++invalid;
        } else {
          if (v != 0.0f) ++nonzero;
          sum += v;
          min_v = std::min(min_v, double(v));
          max_v = std::max(max_v, double(v));
        }
        if (std::memcmp(&out_first[i], &out_last[i], 4) != 0) ++bit_diff;
      }

      std::sort(wall_ms.begin(), wall_ms.end());
      std::sort(gpu_ms.begin(), gpu_ms.end());
      double wall_mean = std::accumulate(wall_ms.begin(), wall_ms.end(), 0.0) / iters;
      double wall_med = wall_ms[iters / 2];
      double wall_p90 = wall_ms[size_t(iters * 0.90)];
      double wall_p99 = wall_ms[size_t(iters * 0.99)];

      double gpu_mean = std::accumulate(gpu_ms.begin(), gpu_ms.end(), 0.0) / iters;
      double gpu_med = gpu_ms[iters / 2];
      double gpu_p90 = gpu_ms[size_t(iters * 0.90)];
      double gpu_p99 = gpu_ms[size_t(iters * 0.99)];

      uint64_t hash64 = Fnv1a64(out_last.data(), out_last.size() * sizeof(float));

      hip_reference::LayerBenchmark::Describe(net);
      std::printf("[RESULT] %s\n", c.label);
      std::printf("  Validity : invalid=%zu nonzero=%zu/%zu bit_diff_first_last=%zu fnv1a64=%016llx\n",
                  invalid, nonzero, out_last.size(), bit_diff, static_cast<unsigned long long>(hash64));
      std::printf("  Range    : min=%.6f max=%.6f mean=%.6f\n", min_v, max_v, sum / out_last.size());
      std::printf("  GPU  (ms): mean=%.3f median=%.3f p90=%.3f p99=%.3f min=%.3f max=%.3f\n",
                  gpu_mean, gpu_med, gpu_p90, gpu_p99, gpu_ms.front(), gpu_ms.back());
      std::printf("  Wall (ms): mean=%.3f median=%.3f p90=%.3f p99=%.3f min=%.3f max=%.3f\n",
                  wall_mean, wall_med, wall_p90, wall_p99, wall_ms.front(), wall_ms.back());
      std::fflush(stdout);

      if(std::getenv("DLSS5_BENCH_PROFILE") && !net.GraphEnabled()) hip_reference::LayerBenchmark::Run(net,d_in,d_out);
      if(net.GraphEnabled() && std::getenv("DLSS5_BENCH_GRAPH_VALIDATE")) hip_reference::LayerBenchmark::ValidateGraphInput(net,d_in,d_out,host_in,out_last);
      api.hipEventDestroy(ev_start);
      api.hipEventDestroy(ev_stop);
      api.hipFree(d_in);
      api.hipFree(d_out);

      if (invalid > 0 || nonzero == 0 || bit_diff > 0) {
        throw std::runtime_error(std::string("validation failed for ") + c.label);
      }
    }

    std::printf("\nALL SELECTED MODEL/RESOLUTION BENCHMARKS PASSED!\n");
    return 0;
  } catch (const std::exception& e) {
    std::fprintf(stderr, "BENCHMARK FAILED: %s\n", e.what());
    return 1;
  }
}

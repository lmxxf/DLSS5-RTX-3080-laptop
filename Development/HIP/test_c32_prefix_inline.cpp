// c32_fast_ffn_attention_fused_half_prefix_finish_main8 (prefix inlined into block 0) against dlss5_prefix_fast_fused_raster +
// c32_fast_ffn_attention_fused_half_finish_main8: synthetic RGBA raster and history, seeds 0/123, temporal 0/1, 400x256 and
// 160x64. main8 bytes and down floats must match bit for bit.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;U ws[]={400,160},hs[]={256,64};
 for(int gi=0;gi<2;gi++)for(U seed:{0u,123u})for(U temporal:{0u,1u}){U W=ws[gi],H=hs[gi],N=W*H,windows=N/64;
  std::vector<float>rgba(size_t(N)*4),hist(size_t(N)*4);for(size_t i=0;i<rgba.size();i++){rgba[i]=float((i*37+i/29+seed)%1001)/1000.f;hist[i]=float((i*53+i/17+7)%997)/996.f;}
  auto c=n.Upload(rgba.data(),rgba.size()*4),h=n.Upload(hist.data(),hist.size()*4);auto fw=n.PackedC32Weight("block0-ffn.f32",false),aw=n.PackedC32Weight("block0-attention.f32",true);
  auto prefix=n.New(size_t(N)*32);n.Run("prefix_fast","dlss5_prefix_fast_fused_raster",size_t(N)*32,n.P(c),n.P(h),n.Weight("block0-ffn.f32"),n.P(prefix),W,H,seed,temporal);
  auto m1=n.New(size_t(N)*8),d1=n.New(size_t(N/4)*32),m2=n.New(size_t(N)*8),d2=n.New(size_t(N/4)*32);
  n.Run("c32_fused_ffn","c32_fast_ffn_attention_fused_half_finish_main8",windows,n.P(prefix),fw,aw,n.P(m1),n.P(d1),windows,U(0),U(1),W,H);
  n.Run("c32_fused_ffn","c32_fast_ffn_attention_fused_half_prefix_finish_main8",windows,n.P(c),n.P(h),fw,aw,n.P(m2),n.P(d2),windows,U(0),U(1),W,H,seed,temporal);n.Synchronize();
  std::vector<unsigned char>a(size_t(N)*32),b(a.size());std::vector<float>x(size_t(N/4)*32),y(x.size());
  n.api.Check(n.api.hipMemcpy(a.data(),n.P(m1),a.size(),2),"main8 ref");n.api.Check(n.api.hipMemcpy(b.data(),n.P(m2),b.size(),2),"main8 inline");n.api.Check(n.api.hipMemcpy(x.data(),n.P(d1),x.size()*4,2),"down ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(d2),y.size()*4,2),"down inline");
  size_t md=0,dd=0,bad=0;for(size_t i=0;i<a.size();i++){md+=a[i]!=b[i];bad+=((a[i]&127)==127)||((b[i]&127)==127);}for(size_t i=0;i<x.size();i++){dd+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}
  printf("%ux%u seed=%u temporal=%u main8_bytediff=%zu down_bitdiff=%zu invalid=%zu\n",W,H,seed,temporal,md,dd,bad);ok=ok&&!md&&!dd&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_c32_prefix_inline ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_c32=o.fused_ffn=o.packed_c32=o.fast_prefix=o.prefix_fused=o.half_c32=o.packed_weights=o.mapped_c32=o.crop_c32=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"prefix inline matches\n":"prefix inline MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

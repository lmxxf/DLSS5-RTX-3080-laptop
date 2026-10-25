#define main phase15_unused_benchmark_main
#include "base_benchmark.cpp"
#undef main
#include <limits>
int main(int argc,char**argv){try{
 if(argc<7)throw std::runtime_error("usage ASSETS MODULES W H OUTPUT_DIR INPUT_RGBA32...");
 const std::string assets=argv[1],mods=argv[2],dir=argv[5];unsigned w=unsigned(std::stoul(argv[3])),h=unsigned(std::stoul(argv[4]));
 // Same production options/environment as the pinned Small31 benchmark.
 setenv("DLSS5_HIP_FAST","1",1);setenv("DLSS5_FAST_NUMERIC","1",1);setenv("DLSS5_HIP_WAVE_OWNED","1",1);setenv("DLSS5_HIP_C512_M32","1",1);setenv("DLSS5_HIP_VIT_PROJ_N64","1",1);setenv("DLSS5_HIP_PDL","1",1);setenv("DLSS5_HIP_VIT_STREAM","3",1);setenv("DLSS5_HIP_SWIN_RUN","1",1);setenv("DLSS5_STYLE","1",1);setenv("DLSS5_VIT_ADAPTIVE","0",1);setenv("DLSS5_MULTI_PASS_PREDICT","0",1);setenv("DLSS5_MULTI_PASS_SKIN_PROTECT","0",1);setenv("DLSS5_MULTI_PASS","0.5",1);dlss5_mode::Request(0);
 auto opt=MakeProductionOptions(w,h,mods,assets);opt.small_geometry=true;opt.graph=false;
 hip_reference::Network net(opt);auto&api=net.Runtime();net.PrepareForExternalInput(false);
 size_t pixels=size_t(w)*h;std::vector<std::vector<float>> inputs;
 for(int i=6;i<argc;i++){
  std::ifstream f(argv[i],std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(pixels*16))throw std::runtime_error("input size");std::vector<float>a(pixels*4);f.seekg(0);f.read((char*)a.data(),pixels*16);
  for(size_t j=0;j<a.size();j++)if(!std::isfinite(a[j])||(j%4==3?a[j]!=1.f:(a[j]<0||a[j]>1)))throw std::runtime_error("working surface domain");inputs.push_back(std::move(a));
 }
 void*in{};void*out{};api.Check(api.hipMalloc(&in,pixels*16),"in");api.Check(api.hipMalloc(&out,pixels*12),"out");
 std::vector<float>sentinel(pixels*3,std::numeric_limits<float>::quiet_NaN());std::vector<std::vector<float>> first(inputs.size());std::vector<unsigned>seen(inputs.size());
 std::vector<unsigned>seq;for(unsigned repeat=0;repeat<2;repeat++)for(unsigned i=0;i<inputs.size();i++)seq.push_back(i);seq.push_back(0);
 for(unsigned frame=0;frame<seq.size();frame++){
  unsigned id=seq[frame];api.Check(api.hipMemcpy(in,inputs[id].data(),pixels*16,1),"upload entire input");api.Check(api.hipMemcpy(out,sentinel.data(),pixels*12,1),"poison output");net.Enqueue(in,nullptr,out,0);net.Synchronize();std::vector<float>b(pixels*3);api.Check(api.hipMemcpy(b.data(),out,pixels*12,2),"read");
  size_t invalid=0,diff=0;for(size_t i=0;i<b.size();i++){invalid+=!std::isfinite(b[i]);if(seen[id])diff+=std::memcmp(&b[i],&first[id][i],4)!=0;}
  if(!seen[id]){first[id]=b;std::ofstream f(dir+"/"+std::to_string(id)+".rgb32",std::ios::binary);f.write((char*)b.data(),pixels*12);}++seen[id];
  printf("FRAME index=%u input=%u invalid=%zu repeat_bitdiff=%zu hash=%016llx\n",frame,id,invalid,diff,(unsigned long long)Fnv1a64(b.data(),pixels*12));fflush(stdout);
  if(invalid||diff)throw std::runtime_error("dynamic input repeat/finite gate");
 }
 api.Check(api.hipMemcpy(in,inputs[0].data(),pixels*16,1),"resource input");unsigned kinds=hip_reference::LayerBenchmark::ResourceOnly(net,in,out);std::vector<float>after(pixels*3);api.Check(api.hipMemcpy(after.data(),out,pixels*12,2),"profile output");if(std::memcmp(after.data(),first[0].data(),pixels*12))throw std::runtime_error("resource instrumentation changed output");
 hip_reference::LayerBenchmark::Describe(net);printf("REGRESSION_PASS inputs=%zu frames=%zu active_kinds=%u resource_output_bitdiff=0\n",inputs.size(),seq.size(),kinds);api.hipFree(in);api.hipFree(out);return 0;
}catch(const std::exception&e){fprintf(stderr,"REGRESSION_FAIL %s\n",e.what());return 1;}}

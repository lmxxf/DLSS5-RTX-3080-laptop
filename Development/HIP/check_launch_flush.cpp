// Per-launch cost of a near-empty kernel after the L2 has been dirtied by a large writer, versus after a clean L2.
// If every kernel boundary carries an L2 writeback (system-scope release), the first empty launch after the writer
// costs far more than the later ones. Two writer targets: device memory (hipMalloc) and host-coherent memory
// (hipHostMalloc), since ROCclr picks fence scopes from the memory a kernel touches.
#include "hip_api.h"
#include <chrono>
#include <vector>
#include <algorithm>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("check_launch_flush DEEP_MODULE");
 hip_probe::Api a(7);a.Check(a.hipInit(0),"init");a.Check(a.hipSetDevice(0),"device");
 hip_probe::Handle stream{},module{},fn{};a.Check(a.hipStreamCreate(&stream),"stream");a.Check(a.hipModuleLoad(&module,argv[1]),"module");a.Check(a.hipModuleGetFunction(&fn,module,"vit_pack_input"),"function");
 unsigned small=256,big=8u<<20;void*sin{},*sout{},*bin{},*bout_dev{},*bout_host{};
 a.Check(a.hipMalloc(&sin,size_t(small)*4),"sin");a.Check(a.hipMalloc(&sout,small),"sout");a.Check(a.hipMalloc(&bin,size_t(big)*4),"bin");a.Check(a.hipMalloc(&bout_dev,big),"bout");a.Check(a.hipHostMalloc(&bout_host,big,0),"bout host");
 a.Check(a.hipMemsetAsync(sin,0,size_t(small)*4,stream),"zero");a.Check(a.hipMemsetAsync(bin,0,size_t(big)*4,stream),"zero big");
 void*eargs[]={&sin,&sout,&small},*dargs[]={&bin,&bout_dev,&big},*hargs[]={&bin,&bout_host,&big};
 auto empty=[&]{a.Check(a.hipModuleLaunchKernel(fn,1,1,1,256,1,1,0,stream,eargs,nullptr),"empty");};
 auto dirty=[&](bool host){a.Check(a.hipModuleLaunchKernel(fn,big/1024,1,1,256,1,1,0,stream,host?hargs:dargs,nullptr),"dirty");};
 for(int i=0;i<20;i++){dirty(false);empty();}a.Check(a.hipStreamSynchronize(stream),"warm");
 auto time=[&](auto seq,unsigned reps){std::vector<double>w;for(unsigned t=0;t<5;t++){auto s=std::chrono::steady_clock::now();for(unsigned i=0;i<reps;i++)seq();a.Check(a.hipStreamSynchronize(stream),"sync");w.push_back(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-s).count());}std::sort(w.begin(),w.end());return w[w.size()/2];};
 const unsigned R=100;
 double e=time([&]{empty();},R),d=time([&]{dirty(false);},R),de=time([&]{dirty(false);empty();},R),de4=time([&]{dirty(false);empty();empty();empty();empty();},R);
 double h=time([&]{dirty(true);},R),he=time([&]{dirty(true);empty();},R),he4=time([&]{dirty(true);empty();empty();empty();empty();},R);
 printf("empty_alone_us=%.2f\n",e*1000/R);
 printf("device_writer: dirty_us=%.1f first_empty_after_dirty_us=%.2f later_empty_us=%.2f\n",d*1000/R,(de-d)*1000/R,(de4-de)*1000/(3*R));
 printf("host_writer:   dirty_us=%.1f first_empty_after_dirty_us=%.2f later_empty_us=%.2f\n",h*1000/R,(he-h)*1000/R,(he4-he)*1000/(3*R));
 return 0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

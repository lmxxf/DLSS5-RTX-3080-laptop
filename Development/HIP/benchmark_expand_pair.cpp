// Compare two independently compiled vit_expand modules. GPU execution is opt-in.
#include "hip_api.h"
#include <vector>
#include <cstdio>
#include <cstring>
#include <chrono>
#include <stdexcept>
using hip_probe::Handle;
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("usage: benchmark_expand_pair.exe BASE.hsaco PAIR.hsaco");
 hip_probe::Api api;api.Check(api.hipInit(0),"init");api.Check(api.hipSetDevice(0),"device");
 Handle mod[2]{},fn[2]{},stream{};api.Check(api.hipStreamCreate(&stream),"stream");
 for(int v=0;v<2;v++){api.Check(api.hipModuleLoad(&mod[v],argv[v+1]),"module");api.Check(api.hipModuleGetFunction(&fn[v],mod[v],"vit_expand"),"function");}
 for(unsigned tokens:{16u,400u,1600u}){
 unsigned inputs=1024,outputs=4096;
 std::vector<float>in(size_t(tokens)*inputs),weights(size_t(inputs)*outputs),a(size_t(tokens)*outputs),b(a.size());
 // Exact E4M3 values, mixed signs and magnitudes. Packed matrix bytes use
 // known encodings rather than sharing the kernel's conversion implementation.
 unsigned codes[]={0,0x38,0xb8,0x30,0xb0,0x20,0xa0,1,0x81};
 float values[]={0,1,-1,.5f,-.5f,.125f,-.125f,1.f/512,-1.f/512};
 for(size_t i=0;i<in.size();i++)in[i]=values[(i*37+i/17)%9];
 auto*w=reinterpret_cast<unsigned char*>(weights.data());
 for(size_t i=0;i<size_t(inputs)*outputs;i++)w[i]=codes[(i*53+i/31)%9];
 void *di{},*dw{},*out{};
 api.Check(api.hipMalloc(&di,in.size()*4),"input");api.Check(api.hipMalloc(&dw,weights.size()*4),"weights");api.Check(api.hipMalloc(&out,a.size()*4),"output");
 api.Check(api.hipMemcpy(di,in.data(),in.size()*4,1),"copy");api.Check(api.hipMemcpy(dw,weights.data(),weights.size()*4,1),"copy");
 auto run=[&](int variant){void*args[]={&di,&dw,&out,&tokens,&inputs,&outputs};api.Check(api.hipModuleLaunchKernel(fn[variant],tokens*outputs/256,1,1,32,1,1,0,stream,args,nullptr),"launch");};
 for(int variant=0;variant<2;variant++){api.Check(api.hipMemsetAsync(out,0xff,a.size()*4,stream),"sentinel");run(variant);api.Check(api.hipStreamSynchronize(stream),"sync");api.Check(api.hipMemcpy(variant?b.data():a.data(),out,a.size()*4,2),"read");}
 size_t diff=0;for(size_t i=0;i<a.size();i++)diff+=memcmp(&a[i],&b[i],4)!=0;
 printf("tokens=%u bitdiff=%zu\n",tokens,diff);if(diff)throw std::runtime_error("output mismatch");
 // ABBA, batch wall time avoids unreliable per-kernel HIP event intervals.
 for(int variant:{0,1,1,0}){for(int i=0;i<3;i++)run(variant);api.Check(api.hipStreamSynchronize(stream),"warm");auto start=std::chrono::steady_clock::now();for(int i=0;i<40;i++)run(variant);api.Check(api.hipStreamSynchronize(stream),"time");printf("tokens=%u variant=%d batch_ms_per_call=%.6f\n",tokens,variant,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/40);fflush(stdout);}
 api.hipFree(di);api.hipFree(dw);api.hipFree(out);
 }
 for(auto m:mod)api.hipModuleUnload(m);api.hipStreamDestroy(stream);return 0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

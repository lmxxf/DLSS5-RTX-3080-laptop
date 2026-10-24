#include "hip_api.h"
#include <chrono>
#include <vector>
#include <cmath>
#include <algorithm>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("check_event_timing DEEP_MODULE");
 hip_probe::Api a(7);a.Check(a.hipInit(0),"init");a.Check(a.hipSetDevice(0),"device");int version=0;a.Check(a.hipRuntimeGetVersion(&version),"version");printf("runtime=%d\n",version);
 hip_probe::Handle stream{},module{},fn{},begin{},end{};void*input{},*output{};unsigned count=1u<<20;
 a.Check(a.hipStreamCreate(&stream),"stream");a.Check(a.hipModuleLoad(&module,argv[1]),"module");a.Check(a.hipModuleGetFunction(&fn,module,"vit_pack_input"),"function");a.Check(a.hipMalloc(&input,size_t(count)*4),"input");a.Check(a.hipMalloc(&output,count),"output");a.Check(a.hipMemsetAsync(input,0,size_t(count)*4,stream),"zero input");a.Check(a.hipMemsetAsync(output,255,count,stream),"poison output");a.Check(a.hipEventCreate(&begin),"begin event");a.Check(a.hipEventCreate(&end),"end event");
 void*args[]={&input,&output,&count};auto launch=[&]{a.Check(a.hipModuleLaunchKernel(fn,(count+255)/256,1,1,256,1,1,0,stream,args,nullptr),"launch");};for(int i=0;i<10;i++)launch();a.Check(a.hipStreamSynchronize(stream),"warm completion");
 bool valid=true;for(unsigned repeats:{1u,8u,64u,256u})for(unsigned trial=0;trial<5;trial++){
  auto t=std::chrono::steady_clock::now();a.Check(a.hipEventRecord(begin,stream),"start");for(unsigned i=0;i<repeats;i++)launch();a.Check(a.hipEventRecord(end,stream),"stop");a.Check(a.hipStreamSynchronize(stream),"completion");double wall=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count();float ms=-1,self=-1;a.Check(a.hipEventElapsedTime(&ms,begin,end),"elapsed");a.Check(a.hipEventElapsedTime(&self,end,end),"self elapsed");valid=valid&&std::isfinite(ms)&&ms>=0&&std::isfinite(self)&&self==0;printf("repeats=%u trial=%u event_ms=%.6f wall_ms=%.6f self_ms=%.6f\n",repeats,trial,ms,wall,self);
 }
 std::vector<unsigned char>bytes(count);a.Check(a.hipMemcpy(bytes.data(),output,count,2),"read output");size_t bad=std::count_if(bytes.begin(),bytes.end(),[](unsigned char v){return v!=0;});printf("event_values_valid=%u incorrect_output=%zu\n",valid,bad);
 a.Check(a.hipEventDestroy(begin),"destroy begin");a.Check(a.hipEventDestroy(end),"destroy end");a.Check(a.hipFree(input),"free input");a.Check(a.hipFree(output),"free output");a.Check(a.hipModuleUnload(module),"unload");a.Check(a.hipStreamDestroy(stream),"destroy stream");return valid&&!bad?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

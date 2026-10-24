// Per-launch GPU-side cost of back-to-back dependent kernels on one stream: a one-workgroup vit_pack_input (256 items,
// ~no work) launched N times, wall clock from first launch to stream completion. per_launch=(t_N-t_1)/(N-1) is the
// floor every extra kernel boundary costs the frame regardless of its work. Not a measure of any kernel's runtime.
#include "hip_api.h"
#include <chrono>
#include <vector>
#include <algorithm>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("check_launch_gap DEEP_MODULE");
 hip_probe::Api a(7);a.Check(a.hipInit(0),"init");a.Check(a.hipSetDevice(0),"device");
 hip_probe::Handle stream{},module{},fn{};void*input{},*output{};unsigned count=256;
 a.Check(a.hipStreamCreate(&stream),"stream");a.Check(a.hipModuleLoad(&module,argv[1]),"module");a.Check(a.hipModuleGetFunction(&fn,module,"vit_pack_input"),"function");
 a.Check(a.hipMalloc(&input,size_t(count)*4),"input");a.Check(a.hipMalloc(&output,count),"output");a.Check(a.hipMemsetAsync(input,0,size_t(count)*4,stream),"zero");
 void*args[]={&input,&output,&count};auto launch=[&]{a.Check(a.hipModuleLaunchKernel(fn,1,1,1,256,1,1,0,stream,args,nullptr),"launch");};
 for(int i=0;i<50;i++)launch();a.Check(a.hipStreamSynchronize(stream),"warm");
 for(unsigned repeats:{1u,16u,64u,259u,1024u}){std::vector<double>wall;
  for(unsigned trial=0;trial<7;trial++){auto t=std::chrono::steady_clock::now();for(unsigned i=0;i<repeats;i++)launch();a.Check(a.hipStreamSynchronize(stream),"completion");wall.push_back(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count());}
  std::sort(wall.begin(),wall.end());printf("launches=%u wall_ms_min=%.4f median=%.4f per_launch_us=%.2f\n",repeats,wall.front(),wall[wall.size()/2],wall[wall.size()/2]*1000.0/repeats);
 }
 a.Check(a.hipFree(input),"free input");a.Check(a.hipFree(output),"free output");a.Check(a.hipModuleUnload(module),"unload");a.Check(a.hipStreamDestroy(stream),"destroy stream");return 0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

#include "hip_api.h"
#include <vector>
#include <string>
#include <fstream>
#include <cstdio>
#include <cstring>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_diagonal MODULE ASSETS");
 std::vector<float>scales;
 for(int block:{2,3,4,67,68,69}){std::ifstream f(std::string(argv[2])+"/block"+std::to_string(block)+"-ffn.f32",std::ios::binary);if(!f)throw std::runtime_error("weights");f.seekg(8704*4);float v[32];if(!f.read((char*)v,sizeof v))throw std::runtime_error("scale read");scales.insert(scales.end(),v,v+32);}
 hip_probe::Api api;api.Check(api.hipInit(0),"init");api.Check(api.hipSetDevice(0),"device");hip_probe::Handle mod{},fn{};api.Check(api.hipModuleLoad(&mod,argv[1]),"module");api.Check(api.hipModuleGetFunction(&fn,mod,"diagonal_probe"),"fn");
 unsigned n=scales.size();void*in{},*out{};std::vector<unsigned>result(size_t(n)*256*3);api.Check(api.hipMalloc(&in,n*4),"alloc");api.Check(api.hipMalloc(&out,result.size()*4),"alloc");api.Check(api.hipMemcpy(in,scales.data(),n*4,1),"copy");void*args[]={&in,&out,&n};api.Check(api.hipModuleLaunchKernel(fn,n*256,1,1,32,1,1,0,nullptr,args,nullptr),"launch");api.Check(api.hipDeviceSynchronize(),"sync");api.Check(api.hipMemcpy(result.data(),out,result.size()*4,2),"read");unsigned bad=0;for(unsigned i=0;i<n*256;i++)if(result[i*3]){if(bad<8)printf("scale=%u value=%.9g fp8=%02x lanes=%08x wmma=%08x scalar=%08x\n",i/256,scales[i/256],i%256,result[i*3],result[i*3+1],result[i*3+2]);bad++;}
 printf("scales=%u finite_cases=%u mismatched_cases=%u\n",n,n*254,bad);api.hipFree(in);api.hipFree(out);api.hipModuleUnload(mod);return bad?1:0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

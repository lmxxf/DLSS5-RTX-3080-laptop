#include "hip_api.h"
#include <vector>
#include <string>
#include <fstream>
#include <cstdio>
#include <cstring>
#include <algorithm>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_mh_diagonal MODULE ASSETS");
 std::vector<float>scales;
 for(int block=5;block<=65;block++){int c=block<=8||block>=62?64:block<=14||(block>=56&&block<=61)?128:256;if(block>=23&&block<=47)continue;std::ifstream f(std::string(argv[2])+"/block"+std::to_string(block)+"-attention.f32",std::ios::binary);if(!f)throw std::runtime_error("weights");f.seekg((4*c*c+(c/32)*4096+c/32)*4);std::vector<float>v(c);if(!f.read((char*)v.data(),c*4))throw std::runtime_error("scale read");scales.insert(scales.end(),v.begin(),v.end());}

 hip_probe::Api api;api.Check(api.hipInit(0),"init");api.Check(api.hipSetDevice(0),"device");hip_probe::Handle mod{},fn{};api.Check(api.hipModuleLoad(&mod,argv[1]),"module");api.Check(api.hipModuleGetFunction(&fn,mod,"mh_diagonal_probe"),"fn");
 unsigned n=scales.size();void*in{},*out{};std::vector<unsigned>result(size_t(n)*256*3*3);api.Check(api.hipMalloc(&in,n*4),"alloc");api.Check(api.hipMalloc(&out,result.size()*4),"alloc");api.Check(api.hipMemcpy(in,scales.data(),n*4,1),"copy");for(unsigned first=0;first<n;first+=128){unsigned batch=std::min(128u,n-first);void*ip=(char*)in+first*4;void*op=(char*)out+size_t(first)*256*3*3*4;void*args[]={&ip,&op,&batch};api.Check(api.hipModuleLaunchKernel(fn,batch*256*3,1,1,32,1,1,0,nullptr,args,nullptr),"launch");api.Check(api.hipDeviceSynchronize(),"sync");}api.Check(api.hipMemcpy(result.data(),out,result.size()*4,2),"read");unsigned bad=0;for(unsigned i=0;i<n*256*3;i++)if(result[i*3]){if(bad<8)printf("scale=%u value=%.9g fp8=%02x lanes=%08x wmma=%08x scalar=%08x\n",i/(256*3),scales[i/(256*3)],(i/3)%256,result[i*3],result[i*3+1],result[i*3+2]);bad++;}
 printf("scales=%u finite_cases=%u mismatched_cases=%u\n",n,n*254*3,bad);api.hipFree(in);api.hipFree(out);api.hipModuleUnload(mod);return bad?1:0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

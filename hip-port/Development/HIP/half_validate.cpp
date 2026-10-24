#include "hip_api.h"
#include <vector>
#include <cstring>
#include <cmath>
#include <cstdio>
using namespace hip_probe;
static float f32(unsigned u){float x;memcpy(&x,&u,4);return x;}
int main(int argc,char**argv){try{if(argc!=2)return 2;std::vector<float>input;input.reserve(1100000);unsigned state=123456789;
for(unsigned i=0;i<1000000;i++){state=1664525*state+1013904223;unsigned b=state;if((b&0x7f800000u)==0x7f800000u)b^=0x00800000u;input.push_back(f32(b));}
for(unsigned i=0x33000000;i<0x48000000;i+=0x1000){input.push_back(f32(i));input.push_back(f32(i-1));input.push_back(f32(i+1));}
Api api;api.Check(api.hipInit(0),"init");api.Check(api.hipSetDevice(0),"device");Handle mod{},fn{};api.Check(api.hipModuleLoad(&mod,argv[1]),"module");api.Check(api.hipModuleGetFunction(&fn,mod,"half_probe"),"kernel");void*in{},*out{};unsigned n=input.size();api.Check(api.hipMalloc(&in,size_t(n)*4),"input");api.Check(api.hipMalloc(&out,size_t(n)*16),"output");api.Check(api.hipMemcpy(in,input.data(),size_t(n)*4,1),"upload");void*args[]={&in,&out,&n};api.Check(api.hipModuleLaunchKernel(fn,(n+255)/256,1,1,256,1,1,0,nullptr,args,nullptr),"launch");api.Check(api.hipDeviceSynchronize(),"wait");std::vector<unsigned>r(size_t(n)*4);api.Check(api.hipMemcpy(r.data(),out,r.size()*4,2),"read");for(unsigned c=1;c<4;c++){size_t bad=0;for(unsigned i=0;i<n;i++)if(r[i*4]!=r[i*4+c]){if(bad<8)printf("variant=%u input=%a ref=%08x got=%08x\n",c,input[i],r[i*4],r[i*4+c]);bad++;}printf("variant=%u count=%u bitdiff=%zu\n",c,n,bad);}api.hipFree(in);api.hipFree(out);api.hipModuleUnload(mod);return 0;}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

#include "hip_api.h"
#include <vector>
#include <cstring>
#include <cstdio>
#include <cmath>
#include <cstdint>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage: test_rtz.exe probe.hsaco");
 std::vector<uint32_t>bits;
 // Every finite half value and adjacent binary32 values, both signs.
 for(unsigned h=0;h<0x7c00;h++){
  unsigned e=h>>10,m=h&1023;float x=e?std::ldexp(1.f+float(m)/1024,int(e)-15):std::ldexp(float(m),-24);
  uint32_t b;memcpy(&b,&x,4);
  for(int d=-1;d<=1;d++)if(b||d>=0){uint32_t v=b+d;bits.push_back(v);bits.push_back(v|0x80000000u);}
 }
 uint32_t seed=123;for(unsigned i=0;i<1000000;i++){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;if((seed&0x7f800000u)!=0x7f800000u)bits.push_back(seed);}
 hip_probe::Api api;api.Check(api.hipInit(0),"init");api.Check(api.hipSetDevice(0),"device");hip_probe::Handle mod{},fn{};api.Check(api.hipModuleLoad(&mod,argv[1]),"module");api.Check(api.hipModuleGetFunction(&fn,mod,"rtz_probe"),"function");
 void*in{},*out{};unsigned n=unsigned(bits.size());api.Check(api.hipMalloc(&in,n*4),"alloc");api.Check(api.hipMalloc(&out,n*4),"alloc");api.Check(api.hipMemcpy(in,bits.data(),n*4,1),"copy");void*args[]={&in,&out,&n};api.Check(api.hipModuleLaunchKernel(fn,(n+255)/256,1,1,256,1,1,0,nullptr,args,nullptr),"launch");api.Check(api.hipDeviceSynchronize(),"sync");std::vector<unsigned>got(n);api.Check(api.hipMemcpy(got.data(),out,n*4,2),"read");
 size_t diff=0;for(unsigned i=0;i<n;i++){unsigned a=bits[i]&0x7fffffffu,s=(bits[i]>>16)&0x8000u;int e=int(a>>23)-127;unsigned expected=e>15?s|0x7bffu:e<-24?s:e<-14?s|(((a&0x7fffffu)|0x800000u)>>unsigned(-e-1)):s|((a>>13)-0x1c000u);if(expected!=got[i]){if(diff<5)printf("input=%08x expected=%04x got=%04x\n",bits[i],expected,got[i]);diff++;}}
 printf("finite_inputs=%u bitdiff=%zu\n",n,diff);api.hipFree(in);api.hipFree(out);api.hipModuleUnload(mod);return diff?1:0;
 }catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

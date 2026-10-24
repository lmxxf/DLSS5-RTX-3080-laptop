#include "hip_api.h"
#include <cstdint>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("test_fp8_staging MODULE");
 hip_probe::Api a;a.Check(a.hipInit(0),"init");int count=0;a.Check(a.hipGetDeviceCount(&count),"count");int dev=-1;
 for(int i=0;i<count;i++){auto p=a.Properties(i);if(std::string(p.gcnArchName).find("gfx1201")==0){dev=i;break;}}if(dev<0)throw std::runtime_error("gfx1201 not found");a.Check(a.hipSetDevice(dev),"device");
 hip_probe::Handle m{},f{};a.Check(a.LoadModule(&m,argv[1]),"module");a.Check(a.hipModuleGetFunction(&f,m,"roundtrip"),"function");
 void*out{};a.Check(a.hipMalloc(&out,256*4),"alloc");void*args[]={&out};a.Check(a.hipModuleLaunchKernel(f,1,1,1,256,1,1,0,nullptr,args,nullptr),"launch");a.Check(a.hipDeviceSynchronize(),"sync");std::vector<unsigned>v(256);a.Check(a.hipMemcpy(v.data(),out,1024,2),"read");
 unsigned errors=0;for(unsigned b=0;b<256;b++){if((b&127)==127){printf("NaN code %u -> %u (not emitted by finite producers)\n",b,v[b]);continue;}if(v[b]!=b){printf("finite roundtrip mismatch %u -> %u\n",b,v[b]);errors++;}}
 a.Check(a.hipFree(out),"free");a.Check(a.hipModuleGetFunction(&f,m,"stage"),"stage function");
 for(unsigned c:{64u,128u,256u}){
  std::vector<unsigned char>input(13*11*c);for(size_t i=0;i<input.size();i++){unsigned b=i%254;input[i]=b>=127?b+1:b;}
  void*in{};a.Check(a.hipMalloc(&in,input.size()),"in alloc");a.Check(a.hipMemcpy(in,input.data(),input.size(),1),"in copy");unsigned n=24*24*(c/4);std::vector<unsigned>words(n*2);a.Check(a.hipMalloc(&out,words.size()*4),"out alloc");void*params[]={&in,&out,&c,&n};a.Check(a.hipModuleLaunchKernel(f,(n+255)/256,1,1,256,1,1,0,nullptr,params,nullptr),"stage launch");a.Check(a.hipDeviceSynchronize(),"stage sync");a.Check(a.hipMemcpy(words.data(),out,words.size()*4,2),"stage copy");unsigned bad=0;
  for(unsigned i=0;i<n;i++){unsigned p=i/(c/4),k=(i%(c/4))*4;int x=int(p%24)-4,y=int(p/24)-5;unsigned expected=0;if(x>=0&&y>=0&&x<13&&y<11)for(unsigned j=0;j<4;j++)expected|=unsigned(input[(y*13+x)*c+k+j])<<(8*j);bad+=words[2*i]!=expected||words[2*i+1]!=expected;}
  printf("C=%u mapped words=%u differences=%u\n",c,n,bad);errors+=bad;a.Check(a.hipFree(in),"free in");a.Check(a.hipFree(out),"free out");
 }
 printf("finite roundtrip + mapped staging errors=%u\n",errors);return errors?1:0;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

#include "hip_api.h"
#include <vector>
#include <algorithm>
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage: test-normalize-rcp.exe MODULE");
 hip_probe::Api a;a.Check(a.hipInit(0),"init");int ndev=0,device=-1;a.Check(a.hipGetDeviceCount(&ndev),"devices");
 for(int i=0;i<ndev;i++){char name[256]{};a.Check(a.hipDeviceGetName(name,256,i),"name");if(std::string(name).find("9070")!=std::string::npos){device=i;break;}}
 if(device<0)throw std::runtime_error("9070 absent");a.Check(a.hipSetDevice(device),"device");
 void*m=nullptr,*k=nullptr,*d=nullptr;a.Check(a.hipModuleLoad(&m,argv[1]),"load");a.Check(a.hipModuleGetFunction(&k,m,"compare_rcp"),"kernel");
 const unsigned chunk=1u<<22,first=0x3b800000,last=0x44834000;std::vector<unsigned>v(chunk);a.Check(a.hipMalloc(&d,chunk*4),"alloc");unsigned long long bad=0,checked=0;unsigned firstbad=0;
 for(unsigned begin=first;begin<=last;){unsigned n=std::min(chunk,last-begin+1);void*args[]={&d,&begin,&n};a.Check(a.hipModuleLaunchKernel(k,(n+255)/256,1,1,256,1,1,0,nullptr,args,nullptr),"launch");a.Check(a.hipDeviceSynchronize(),"sync");a.Check(a.hipMemcpy(v.data(),d,n*4,2),"read");for(unsigned i=0;i<n;i++)if(v[i]){if(!bad)firstbad=begin+i;++bad;}checked+=n;begin+=n;}
 printf("checked=%llu different=%llu first_bad_bits=%08x\n",checked,bad,firstbad);a.Check(a.hipFree(d),"free");a.Check(a.hipModuleUnload(m),"unload");return bad?1:0;
}catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 2;}}

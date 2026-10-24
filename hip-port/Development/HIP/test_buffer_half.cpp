#include "hip_api.h"
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("test_buffer_half MODULE");hip_probe::Api a;a.Check(a.hipInit(0),"init");int count=0,device=-1;a.Check(a.hipGetDeviceCount(&count),"count");for(int i=0;i<count;i++)if(std::string(a.Properties(i).gcnArchName).find("gfx1201")==0){device=i;break;}if(device<0)throw std::runtime_error("gfx1201 absent");a.Check(a.hipSetDevice(device),"device");hip_probe::Handle m{},f{};a.Check(a.LoadModule(&m,argv[1]),"module");a.Check(a.hipModuleGetFunction(&f,m,"probe"),"function");
 unsigned n=65536;std::vector<unsigned short>x(n),r(n),w(n);for(unsigned i=0;i<n;i++)x[i]=i;std::vector<unsigned>v(n*2);void*in{},*rd{},*wr{},*fv{};
 a.Check(a.hipMalloc(&in,n*2),"in");a.Check(a.hipMalloc(&rd,n*2),"rd");a.Check(a.hipMalloc(&wr,n*2),"wr");a.Check(a.hipMalloc(&fv,n*8),"fv");a.Check(a.hipMemcpy(in,x.data(),n*2,1),"input");
 bool correct=false;for(unsigned cfg:{0u,0x20000u,0x27000u,0x31004000u}){
  a.Check(a.hipMemsetAsync(wr,0x55,n*2,nullptr),"sentinel");void*args[]={&in,&rd,&wr,&fv,&n,&cfg};a.Check(a.hipModuleLaunchKernel(f,n/256,1,1,256,1,1,0,nullptr,args,nullptr),"launch");a.Check(a.hipDeviceSynchronize(),"sync");a.Check(a.hipMemcpy(r.data(),rd,n*2,2),"r");a.Check(a.hipMemcpy(w.data(),wr,n*2,2),"w");a.Check(a.hipMemcpy(v.data(),fv,n*8,2),"v");size_t re=0,we=0,fe=0;for(unsigned i=0;i<n;i++){re+=r[i]!=x[i];we+=w[i]!=x[i];if((i&0x7c00)!=0x7c00)fe+=v[2*i]!=v[2*i+1];}printf("cfg=%08x read_bitdiff=%zu store_bitdiff=%zu finite_cvt_bitdiff=%zu\n",cfg,re,we,fe);if(cfg==0x31004000u)correct=!re&&!we&&!fe;
 }
 return correct?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

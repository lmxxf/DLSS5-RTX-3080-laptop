// Diagnostic runner only. Native NGX D3D12 uses NVAPI CuKernelChain, not nvcuda launches.
#include "MinHook.h"
#include <map>
using NvQuery=void*(*)(unsigned);
struct Dim3{unsigned x,y,z;};
struct Kernel{void*function;Dim3 grid,block;unsigned shared;const void*params;unsigned paramSize;};
using CreateModule=int(*)(ID3D12Device*,const void*,unsigned,void**);
using CreateFunction=int(*)(ID3D12Device*,void*,const char*,void**);
using Chain=int(*)(ID3D12GraphicsCommandList*,const Kernel*,unsigned);
static NvQuery real_query=nullptr;static CreateModule real_module=nullptr;static CreateFunction real_function=nullptr;static Chain real_chain=nullptr;
static std::map<void*,std::string> names;static std::map<void*,unsigned> modules;
static FILE*trace=nullptr;static int frame_id=-1;static bool split=false,timed=false;static unsigned chain_id=0,query_count=2;
static ID3D12QueryHeap*prof_heap;static ID3D12Resource*prof_readback;static uint64_t prof_frequency;
struct Record{unsigned chain,index,query;Kernel k;bool has_time;};static std::vector<Record> records;
static int hook_module(ID3D12Device*d,const void*blob,unsigned size,void**out){int r=real_module(d,blob,size,out);if(!r){unsigned id=modules.size();modules[*out]=id;fprintf(trace,"MODULE,%u,%p,%u\n",id,*out,size);}return r;}
static int hook_function(ID3D12Device*d,void*mod,const char*n,void**out){int r=real_function(d,mod,n,out);if(!r){names[*out]=n;fprintf(trace,"FUNCTION,%p,%u,%s\n",*out,modules[mod],n);}return r;}
static int hook_chain(ID3D12GraphicsCommandList*l,const Kernel*k,unsigned n){
 unsigned chain=chain_id++;int result=0;
 if(split&&frame_id>=0){
  for(unsigned i=0;i<n;i++){unsigned q=query_count;query_count+=2;if(timed)l->EndQuery(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,q);int r=real_chain(l,k+i,1);if(timed)l->EndQuery(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,q+1);records.push_back({chain,i,q,k[i],timed});if(r)result=r;}
 }else{
  unsigned q=query_count;query_count+=2;if(timed&&frame_id>=0)l->EndQuery(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,q);result=real_chain(l,k,n);if(timed&&frame_id>=0)l->EndQuery(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,q+1);
  for(unsigned i=0;i<n;i++)records.push_back({chain,i,q,k[i],timed&&frame_id>=0});
 }
 fprintf(trace,"CHAIN,%d,%u,%u,%d\n",frame_id,chain,n,result);return result;
}
static void* hook_query(unsigned id){void*p=real_query(id);fprintf(trace,"QUERY,%08x,%p\n",id,p);
 if(id==0xad1a677d&&p){real_module=(CreateModule)p;return (void*)hook_module;}
 if(id==0xe2436e22&&p){real_function=(CreateFunction)p;return (void*)hook_function;}
 if(id==0x24973538&&p){real_chain=(Chain)p;return (void*)hook_chain;}
 return p;
}
static void profile_init(ID3D12QueryHeap*heap,ID3D12Resource*rb,uint64_t freq){
 const char*path=getenv("V23_TRACE");if(!path)return;trace=fopen(path,"w");if(!trace)ExitProcess(90);timed=getenv("V23_EVENTS")!=nullptr;split=getenv("V23_SPLIT")!=nullptr;prof_heap=heap;prof_readback=rb;prof_frequency=freq;
 HMODULE nv=LoadLibraryW(L"nvapi64.dll");void*nq=(void*)GetProcAddress(nv,"nvapi_QueryInterface");if(!nq||MH_Initialize()!=MH_OK||MH_CreateHook(nq,(void*)hook_query,(void**)&real_query)!=MH_OK||MH_EnableHook(nq)!=MH_OK)ExitProcess(91);
 fprintf(trace,"META,frequency,%llu,split,%d,timing,%d,KernelSize,%zu\n",(unsigned long long)freq,int(split),int(timed),sizeof(Kernel));
}
static void profile_frame_begin(int i){frame_id=i;chain_id=0;query_count=2;records.clear();}
static void profile_resolve(ID3D12GraphicsCommandList*l){if(trace&&timed&&!records.empty()){unsigned count=query_count-2;if(count+2>=4096)ExitProcess(92);l->ResolveQueryData(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,2,count,prof_readback,0);}}
static void profile_frame_end(){if(!trace)return;uint64_t*ts=nullptr;D3D12_RANGE range{0,4096*8};if(timed)prof_readback->Map(0,&range,(void**)&ts);
 for(auto&r:records){double ms=r.has_time?double(ts[r.query-1]-ts[r.query-2])*1000.0/double(prof_frequency):-1.;auto&k=r.k;fprintf(trace,"KERNEL,%d,%u,%u,%s,%u,%u,%u,%u,%u,%u,%u,%.7f,%llu,%llu\n",frame_id,r.chain,r.index,names[k.function].c_str(),k.grid.x,k.grid.y,k.grid.z,k.block.x,k.block.y,k.block.z,k.shared,ms,r.has_time?(unsigned long long)ts[r.query-2]:0,r.has_time?(unsigned long long)ts[r.query-1]:0);}
 if(timed){D3D12_RANGE zero{0,0};prof_readback->Unmap(0,&zero);}fflush(trace);
}

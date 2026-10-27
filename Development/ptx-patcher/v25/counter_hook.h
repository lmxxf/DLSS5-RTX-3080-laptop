// Diagnostic runner only. Native NGX D3D12 uses NVAPI CuKernelChain, not nvcuda launches.
#include "MinHook.h"
#include <map>
#include "counter_ids.h"
static ID3D12Resource *count_gpu=nullptr,*count_zero=nullptr;
static D3D12_RESOURCE_STATES count_state=D3D12_RESOURCE_STATE_COPY_DEST;
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
 if(frame_id==50){for(unsigned j=0;j<n;j++){fprintf(trace,"PARAM,%d,%s,%u,",frame_id,names[k[j].function].c_str(),k[j].paramSize);auto bytes=(const unsigned char*)k[j].params;for(unsigned z=0;bytes&&z<k[j].paramSize;z++)fprintf(trace,"%02x",bytes[z]);fprintf(trace,"\n");}}
 std::vector<Kernel> cloned(k,k+n);std::vector<std::vector<unsigned char>> payload(n);
 for(unsigned j=0;j<n;j++){int id=counter_id(names[k[j].function]);if(id<0)continue;unsigned offset=(k[j].paramSize+7u)&~7u;payload[j].resize(offset+8);memcpy(payload[j].data(),k[j].params,k[j].paramSize);auto address=count_gpu->GetGPUVirtualAddress();memcpy(payload[j].data()+offset,&address,8);cloned[j].params=payload[j].data();cloned[j].paramSize=offset+8;}k=cloned.data();
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
 ID3D12Device*device=nullptr;if(FAILED(rb->GetDevice(IID_PPV_ARGS(&device))))ExitProcess(95);
 auto alloc=[&](D3D12_HEAP_TYPE ht,D3D12_RESOURCE_STATES state,D3D12_RESOURCE_FLAGS flags){D3D12_HEAP_PROPERTIES hp{};hp.Type=ht;D3D12_RESOURCE_DESC d{};d.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;d.Width=4096;d.Height=1;d.DepthOrArraySize=1;d.MipLevels=1;d.SampleDesc.Count=1;d.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;d.Flags=flags;ID3D12Resource*r=nullptr;if(FAILED(device->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&d,state,nullptr,IID_PPV_ARGS(&r))))ExitProcess(96);return r;};
 count_gpu=alloc(D3D12_HEAP_TYPE_DEFAULT,D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);count_zero=alloc(D3D12_HEAP_TYPE_UPLOAD,D3D12_RESOURCE_STATE_GENERIC_READ,D3D12_RESOURCE_FLAG_NONE);void*z=nullptr;D3D12_RANGE range{0,0};count_zero->Map(0,&range,&z);memset(z,0,4096);count_zero->Unmap(0,nullptr);device->Release();
 HMODULE nv=LoadLibraryW(L"nvapi64.dll");void*nq=(void*)GetProcAddress(nv,"nvapi_QueryInterface");if(!nq||MH_Initialize()!=MH_OK||MH_CreateHook(nq,(void*)hook_query,(void**)&real_query)!=MH_OK||MH_EnableHook(nq)!=MH_OK)ExitProcess(91);
 fprintf(trace,"META,frequency,%llu,split,%d,timing,%d,KernelSize,%zu\n",(unsigned long long)freq,int(split),int(timed),sizeof(Kernel));
}
static void count_transition(ID3D12GraphicsCommandList*l,D3D12_RESOURCE_STATES to){if(to==count_state)return;D3D12_RESOURCE_BARRIER b{};b.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;b.Transition={count_gpu,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,count_state,to};l->ResourceBarrier(1,&b);count_state=to;}
static void profile_frame_begin(int i,ID3D12GraphicsCommandList*l){frame_id=i;chain_id=0;query_count=2;records.clear();if(trace){count_transition(l,D3D12_RESOURCE_STATE_COPY_DEST);l->CopyBufferRegion(count_gpu,0,count_zero,0,4096);count_transition(l,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);}}
static void profile_resolve(ID3D12GraphicsCommandList*l){if(trace&&timed&&!records.empty()){unsigned count=query_count-2;l->ResolveQueryData(prof_heap,D3D12_QUERY_TYPE_TIMESTAMP,2,count,prof_readback,0);}if(trace){D3D12_RESOURCE_BARRIER b{};b.Type=D3D12_RESOURCE_BARRIER_TYPE_UAV;b.UAV.pResource=count_gpu;l->ResourceBarrier(1,&b);count_transition(l,D3D12_RESOURCE_STATE_COPY_SOURCE);l->CopyBufferRegion(prof_readback,16384,count_gpu,0,4096);}}
static void profile_frame_end(){if(!trace)return;uint64_t*ts=nullptr;D3D12_RANGE range{0,4096*8};if(timed)prof_readback->Map(0,&range,(void**)&ts);
 for(auto&r:records){double ms=r.has_time?double(ts[r.query-1]-ts[r.query-2])*1000.0/double(prof_frequency):-1.;auto&k=r.k;fprintf(trace,"KERNEL,%d,%u,%u,%s,%u,%u,%u,%u,%u,%u,%u,%.7f,%llu,%llu\n",frame_id,r.chain,r.index,names[k.function].c_str(),k.grid.x,k.grid.y,k.grid.z,k.block.x,k.block.y,k.block.z,k.shared,ms,r.has_time?(unsigned long long)ts[r.query-2]:0,r.has_time?(unsigned long long)ts[r.query-1]:0);}
 if(trace){void*ptr=nullptr;D3D12_RANGE read{16384,20480};prof_readback->Map(0,&read,&ptr);auto values=(const unsigned long long*)((const unsigned char*)ptr+16384);for(unsigned id=0;id<64;id++)for(unsigned j=0;j<8;j++)if(values[id*8+j])fprintf(trace,"COUNT,%d,%u,%u,%llu\n",frame_id,id,j,values[id*8+j]);D3D12_RANGE no_write{0,0};prof_readback->Unmap(0,&no_write);}
 if(timed){D3D12_RANGE zero{0,0};prof_readback->Unmap(0,&zero);}fflush(trace);
}

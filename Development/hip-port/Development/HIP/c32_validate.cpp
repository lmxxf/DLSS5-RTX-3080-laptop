// Usage: c32_validate.exe ASSETS_DIR MODULE_HSACO OUTPUT_PREFIX
// Scalar D3D12 NativePreblockRuntime oracle vs SDKless HIP C32 stages. No deployment.
#include <cmath>
#include <windows.h>
#include <dxgi1_6.h>
#include <d3d12.h>
#include <d3dcompiler.h>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include "hip_api.h"
#include "../../src/native_preblock_runtime.h"
#include "../../src/native_game_submission.h"
using hip_probe::Handle;
static void ck(HRESULT h){if(FAILED(h))throw std::runtime_error("D3D HRESULT="+std::to_string(unsigned(h)));}
static std::wstring wide(const char*s){int n=MultiByteToWideChar(CP_UTF8,0,s,-1,nullptr,0);std::wstring v(n,L'\0');MultiByteToWideChar(CP_UTF8,0,s,-1,v.data(),n);v.resize(n-1);return v;}
static std::vector<float> read(const std::wstring&p,size_t count){std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(count*4))throw std::runtime_error("weight missing/size");f.seekg(0);std::vector<float>v(count);if(!f.read(reinterpret_cast<char*>(v.data()),count*4))throw std::runtime_error("weight read");return v;}
static void save(const std::string&p,const std::vector<float>&v){std::ofstream f(p,std::ios::binary);if(!f.write(reinterpret_cast<const char*>(v.data()),v.size()*4))throw std::runtime_error("save failed "+p);}
static ID3D12Resource* buffer(ID3D12Device*d,size_t bytes,D3D12_HEAP_TYPE heap){D3D12_RESOURCE_DESC desc{};desc.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;desc.Width=bytes;desc.Height=1;desc.DepthOrArraySize=desc.MipLevels=1;desc.SampleDesc.Count=1;desc.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;D3D12_HEAP_PROPERTIES hp{};hp.Type=heap;ID3D12Resource*r=nullptr;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&desc,heap==D3D12_HEAP_TYPE_UPLOAD?D3D12_RESOURCE_STATE_GENERIC_READ:D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&r)));return r;}
static void transition(ID3D12GraphicsCommandList*c,ID3D12Resource*r,D3D12_RESOURCE_STATES a,D3D12_RESOURCE_STATES b){D3D12_RESOURCE_BARRIER v{};v.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;v.Transition={r,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,a,b};c->ResourceBarrier(1,&v);}
static void clear_flags(){wchar_t*env=GetEnvironmentStringsW();std::vector<std::wstring>names;for(auto*p=env;*p;p+=wcslen(p)+1)if(!wcsncmp(p,L"DLSS5_",6)){const wchar_t*e=wcschr(p,L'=');if(e)names.emplace_back(p,size_t(e-p));}FreeEnvironmentStringsW(env);for(auto&n:names)_wputenv((n+L"=").c_str());}
static float fp8(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
struct Comparison {size_t bits{},numeric{},invalid{};double maxabs{};};
static Comparison compare(const std::vector<float>&a,const std::vector<float>&b){if(a.size()!=b.size())throw std::runtime_error("compare size");Comparison r;for(size_t i=0;i<a.size();i++){unsigned x,y;memcpy(&x,&a[i],4);memcpy(&y,&b[i],4);r.bits+=x!=y;r.numeric+=a[i]!=b[i];r.invalid+=!std::isfinite(a[i])||!std::isfinite(b[i]);if(std::isfinite(a[i])&&std::isfinite(b[i]))r.maxabs=std::max(r.maxabs,std::abs(double(a[i])-b[i]));}return r;}
int main(int argc,char**argv){try{
 if(argc!=4&&argc!=5){puts("usage: c32_validate.exe assets-dir module.hsaco output-prefix [wmma-module.hsaco]");return 2;}clear_flags();const auto dir=wide(argv[1]);auto fw=read(dir+L"\\block1-ffn.f32",8736),aw=read(dir+L"\\block1-attention.f32",8225);std::string prefix=argv[3];std::ofstream report(prefix+"-report.txt");
 IDXGIFactory1*factory=nullptr;ck(CreateDXGIFactory1(IID_PPV_ARGS(&factory)));ID3D12Device*d=nullptr;for(unsigned i=0;;i++){IDXGIAdapter1*a=nullptr;if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if((desc.VendorId==0x10de||desc.VendorId==0x1002))D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d));a->Release();if(d)break;}factory->Release();if(!d)throw std::runtime_error("AMD D3D12 adapter missing");
 ID3D12CommandQueue*q=nullptr;D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission submit;submit.Create(q,false);
 hip_probe::Api hip;hip.Check(hip.hipInit(0),"hipInit");hip.Check(hip.hipSetDevice(0),"hipSetDevice");Handle module=nullptr;hip.Check(hip.hipModuleLoad(&module,argv[2]),"module");
 Handle wmodule=nullptr;if(argc==5)hip.Check(hip.hipModuleLoad(&wmodule,argv[4]),"WMMA module");
 const unsigned W=16,H=16,T=W*H,windows=T/64,raw=1;std::vector<void*>allocations;
 auto alloc=[&](size_t count){void*p=nullptr;hip.Check(hip.hipMalloc(&p,count*4),"malloc");allocations.push_back(p);return p;};
 void*hi=alloc(T*32),*hf=alloc(8736),*ha=alloc(8225),*hidden=alloc(T*128),*ffn=alloc(T*32),*qkv=alloc(T*96),*norm=alloc(T*64),*ex=alloc(windows*4096),*prob=alloc(windows*4096),*av=alloc(T*32),*hraw=alloc(T*32),*main=alloc(T*32),*down=alloc(T*8);
 void*wqkv=wmodule?alloc(T*96):nullptr,*wnorm=wmodule?alloc(T*64):nullptr,*wex=wmodule?alloc(windows*4096):nullptr,*wprob=wmodule?alloc(windows*4096):nullptr,*wav=wmodule?alloc(T*32):nullptr,*wraw=wmodule?alloc(T*32):nullptr;
 void*whidden=wmodule?alloc(T*128):nullptr,*wffn=wmodule?alloc(T*32):nullptr,*wisolated=wmodule?alloc(T*32):nullptr;
 hip.Check(hip.hipMemcpy(hf,fw.data(),fw.size()*4,1),"ffn weights");hip.Check(hip.hipMemcpy(ha,aw.data(),aw.size()*4,1),"attention weights");
 auto launch=[&](const char*name,unsigned items,std::initializer_list<void*>args){Handle fn=nullptr;hip.Check(hip.hipModuleGetFunction(&fn,module,name),name);std::vector<void*>p(args);hip.Check(hip.hipModuleLaunchKernel(fn,(items+255)/256,1,1,256,1,1,0,nullptr,p.data(),nullptr),name);};
 size_t totaldiff=0,totalinvalid=0;
 for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>input(T*32);for(unsigned i=0;i<input.size();i++)input[i]=pattern?float(int((i*73+19)%2048)-1024)/512.f:fp8(((i*37+11)%96)|((i%3==0)?128:0));
  std::string base=prefix+"-p"+std::to_string(pattern);save(base+"-input.f32",input);
  auto*source=buffer(d,input.size()*4,D3D12_HEAP_TYPE_UPLOAD);void*m=nullptr;D3D12_RANGE none{};ck(source->Map(0,&none,&m));memcpy(m,input.data(),input.size()*4);source->Unmap(0,nullptr);
  std::vector<std::vector<float>> oracle(4);
  {NativePreblockRuntime stage;stage.Create(d,source,W,H,fw,aw,dir,true,true,nullptr);submit.Submit([&](ID3D12GraphicsCommandList*c){stage.Record(c,0);});submit.Flush();
   ID3D12Resource*outputs[]={stage.FfnTilesForTest(),stage.RawTiles(),stage.Main(),stage.Downsample()};
   for(unsigned j=0;j<4;j++){size_t count=j==3?T*8:T*32;auto*rb=buffer(d,count*4,D3D12_HEAP_TYPE_READBACK);submit.Submit([&](ID3D12GraphicsCommandList*c){transition(c,outputs[j],D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_SOURCE);c->CopyBufferRegion(rb,0,outputs[j],0,count*4);transition(c,outputs[j],D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});submit.Flush();D3D12_RANGE range{0,count*4};ck(rb->Map(0,&range,&m));oracle[j].resize(count);memcpy(oracle[j].data(),m,count*4);rb->Unmap(0,&none);rb->Release();}
  }source->Release();
  hip.Check(hip.hipMemcpy(hi,input.data(),input.size()*4,1),"input upload");
  for(auto pair:{std::pair<void*,size_t>{ffn,T*32},{hraw,T*32},{main,T*32},{down,T*8}})hip.Check(hip.hipMemsetAsync(pair.first,0xff,pair.second*4,nullptr),"sentinel");
  launch("c32_ffn_expand",T*128,{&hi,&hf,&hidden,(void*)&T});launch("c32_ffn_contract",T*32,{&hi,&hidden,&hf,&ffn,(void*)&T,(void*)&raw});
  launch("c32_attn_qkv",T*96,{&ffn,&ha,&qkv,(void*)&T});launch("c32_attn_normalize",T,{&qkv,&ha,&norm,(void*)&T});launch("c32_attn_scores",windows*4096,{&norm,&ha,&ex,(void*)&windows});launch("c32_attn_probabilities",T,{&ex,&prob,(void*)&windows});launch("c32_attn_av",T*32,{&prob,&qkv,&av,(void*)&windows});launch("c32_attn_project",T*32,{&ffn,&av,&ha,&hraw,(void*)&T,(void*)&raw});launch("c32_finish",T*32,{&hraw,&main,&down,(void*)&W,(void*)&H});hip.Check(hip.hipDeviceSynchronize(),"C32 completion");
  const char*names[]={"ffn","raw","main","down"};void*actuals[]={ffn,hraw,main,down};for(unsigned j=0;j<4;j++){std::vector<float>v(oracle[j].size());hip.Check(hip.hipMemcpy(v.data(),actuals[j],v.size()*4,2),"read stage");save(base+"-d3d-"+names[j]+".f32",oracle[j]);save(base+"-hip-"+names[j]+".f32",v);auto r=compare(oracle[j],v);totaldiff+=r.bits;totalinvalid+=r.invalid;printf("pattern=%u stage=%s count=%zu bitdiff=%zu numericdiff=%zu invalid=%zu maxabs=%.9g\n",pattern,names[j],v.size(),r.bits,r.numeric,r.invalid,r.maxabs);report<<"pattern="<<pattern<<" stage="<<names[j]<<" count="<<v.size()<<" bitdiff="<<r.bits<<" numericdiff="<<r.numeric<<" invalid="<<r.invalid<<" maxabs="<<r.maxabs<<"\n";}
  if(wmodule){
   auto wlaunch=[&](const char*name,unsigned items,std::initializer_list<void*>args){Handle fn=nullptr;hip.Check(hip.hipModuleGetFunction(&fn,wmodule,name),name);std::vector<void*>p(args);hip.Check(hip.hipModuleLaunchKernel(fn,(items+255)/256,1,1,32,1,1,0,nullptr,p.data(),nullptr),name);};
   for(auto span:{std::pair<unsigned,unsigned>{512,4096},{4608,4096}})for(unsigned i=span.first;i<span.first+span.second;i++){bool exact=false;for(unsigned b=0;b<256;b++)if((b&127)<127&&fp8(b)==fw[i]){exact=true;break;}if(!exact)throw std::runtime_error("FFN WMMA weight not finite FP8 lattice");}
   hip.Check(hip.hipMemsetAsync(whidden,0xff,T*128*4,nullptr),"WMMA hidden sentinel");hip.Check(hip.hipMemsetAsync(wffn,0xff,T*32*4,nullptr),"WMMA FFN sentinel");hip.Check(hip.hipMemsetAsync(wisolated,0xff,T*32*4,nullptr),"WMMA contract sentinel");
   wlaunch("c32_ffn_expand_wmma",T*128,{&hi,&hf,&whidden,(void*)&T});
   wlaunch("c32_ffn_contract_wmma",T*32,{&hi,&whidden,&hf,&wffn,(void*)&T,(void*)&raw});
   wlaunch("c32_ffn_contract_wmma",T*32,{&hi,&hidden,&hf,&wisolated,(void*)&T,(void*)&raw});
   for(unsigned i=0;i<4096;i++){bool exact=false;for(unsigned b=0;b<256;b++)if((b&127)<127&&fp8(b)==aw[i]){exact=true;break;}if(!exact)throw std::runtime_error("attention WMMA weight not finite FP8 lattice");}
   for(auto span:{std::pair<void*,size_t>{wqkv,T*96},{wnorm,T*64},{wex,windows*4096},{wprob,windows*4096},{wav,T*32},{wraw,T*32}})hip.Check(hip.hipMemsetAsync(span.first,0xff,span.second*4,nullptr),"WMMA attention sentinel");
   wlaunch("c32_attn_qkv_wmma",T*96,{&wffn,&ha,&wqkv,(void*)&T});
   launch("c32_attn_normalize",T,{&wqkv,&ha,&wnorm,(void*)&T});
   wlaunch("c32_attn_scores_wmma",windows*4096,{&wnorm,&ha,&wex,(void*)&windows});
   launch("c32_attn_probabilities",T,{&wex,&wprob,(void*)&windows});
   wlaunch("c32_attn_av_wmma",T*32,{&wprob,&wqkv,&wav,(void*)&windows});
   wlaunch("c32_attn_project_wmma",T*32,{&wffn,&wav,&ha,&wraw,(void*)&T,(void*)&raw});
   hip.Check(hip.hipDeviceSynchronize(),"WMMA C32 completion");
   const char*wnames[]={"hidden","ffn","contract-isolated","qkv","normalized","ex","prob","av","raw"};void*wgpu[]={whidden,wffn,wisolated,wqkv,wnorm,wex,wprob,wav,wraw};void*rgpu[]={hidden,ffn,ffn,qkv,norm,ex,prob,av,hraw};const size_t counts[]={T*128,T*32,T*32,T*96,T*64,windows*4096,windows*4096,T*32,T*32};
   for(unsigned j=0;j<9;j++){size_t count=counts[j];std::vector<float>wv(count),rv(count);hip.Check(hip.hipMemcpy(wv.data(),wgpu[j],count*4,2),"WMMA read");hip.Check(hip.hipMemcpy(rv.data(),rgpu[j],count*4,2),"reference read");save(base+"-wmma-"+wnames[j]+".f32",wv);save(base+"-reference-"+wnames[j]+".f32",rv);auto r=compare(rv,wv);totaldiff+=r.bits;totalinvalid+=r.invalid;printf("pattern=%u stage=wmma-%s count=%zu bitdiff=%zu numericdiff=%zu invalid=%zu maxabs=%.9g\n",pattern,wnames[j],count,r.bits,r.numeric,r.invalid,r.maxabs);report<<"pattern="<<pattern<<" stage=wmma-"<<wnames[j]<<" count="<<count<<" bitdiff="<<r.bits<<" numericdiff="<<r.numeric<<" invalid="<<r.invalid<<" maxabs="<<r.maxabs<<"\n";}
  }
  fflush(stdout);
 }
 hip.Check(hip.hipDeviceSynchronize(),"final sync");for(auto*p:allocations)hip.Check(hip.hipFree(p),"free");hip.Check(hip.hipModuleUnload(module),"unload");if(wmodule)hip.Check(hip.hipModuleUnload(wmodule),"WMMA unload");q->Release();d->Release();printf("RESULT bitdiff=%zu invalid=%zu\n",totaldiff,totalinvalid);return totalinvalid?1:totaldiff?3:0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

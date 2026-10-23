// Usage: deep_validate.exe ASSETS_DIR MODULE_HSACO OUTPUT_PREFIX
// Scalar D3D12 NativeVitBlock oracle vs SDKless HIP ViT64 stages. No deployment.
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
#include "../../src/native_vit_block.h"
#include "../../src/native_game_submission.h"
#include "../../src/native_lab_paths.h"
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
 if(argc!=4&&argc!=5){puts("usage: deep_validate.exe assets-dir deep-module.hsaco output-prefix [deep-wmma-module.hsaco]");return 2;}clear_flags();const auto dir=wide(argv[1]);auto load=[&](const wchar_t*name,size_t count){auto v=NativeReadF32(dir+L"\\"+name,"deep validation weights");if(v.size()!=count)throw std::runtime_error("weight count");return v;};auto ew=load(L"block31-expand.f32",4194304),cw=load(L"block31-contract.f32",4195328),qw=load(L"block31-qkv.f32",3145760),pw=load(L"block31-projection.f32",1049600);std::string prefix=argv[3];std::ofstream report(prefix+"-report.txt");if(!report)throw std::runtime_error("report open");
 IDXGIFactory1*factory=nullptr;ck(CreateDXGIFactory1(IID_PPV_ARGS(&factory)));ID3D12Device*d=nullptr;for(unsigned i=0;;i++){IDXGIAdapter1*a=nullptr;if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if((desc.VendorId==0x10de||desc.VendorId==0x1002))D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d));a->Release();if(d)break;}factory->Release();if(!d)throw std::runtime_error("AMD D3D12 adapter missing");ID3D12CommandQueue*q=nullptr;D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission submit;submit.Create(q,false);
 hip_probe::Api hip(7);hip.Check(hip.hipInit(0),"hipInit");hip.Check(hip.hipSetDevice(0),"hipSetDevice");Handle module=nullptr;hip.Check(hip.hipModuleLoad(&module,argv[2]),"module");Handle wmodule=nullptr;if(argc==5)hip.Check(hip.hipModuleLoad(&wmodule,argv[4]),"WMMA module");std::vector<void*>allocations;auto alloc=[&](size_t n){void*p=nullptr;hip.Check(hip.hipMalloc(&p,n*4),"malloc");allocations.push_back(p);return p;};auto upload=[&](const std::vector<float>&v){void*p=alloc(v.size());hip.Check(hip.hipMemcpy(p,v.data(),v.size()*4,1),"weights upload");return p;};void*he=upload(ew),*hc=upload(cw),*hq=upload(qw),*hp=upload(pw);unsigned T=64,C=1024,E=4096;
 void*hi=alloc(T*C),*hidden=alloc(T*E),*contract=alloc(T*C),*qkv=alloc(T*3*C),*norm=alloc(T*3*C),*ex=alloc(T*32*T),*inv=alloc(T*32),*av=alloc(T*C),*out=alloc(T*C);size_t totaldiff=0,totalinvalid=0;void*scratch=wmodule?alloc(1048576):nullptr;std::string current;unsigned wserial=0;
 auto launch=[&](const char*name,unsigned items,std::initializer_list<void*>args){Handle fn=nullptr;hip.Check(hip.hipModuleGetFunction(&fn,module,name),name);std::vector<void*>p(args);hip.Check(hip.hipModuleLaunchKernel(fn,(items+255)/256,1,1,256,1,1,0,nullptr,p.data(),nullptr),name);hip.Check(hip.hipDeviceSynchronize(),name);
  if(!wmodule)return;std::string key=name;unsigned index=99,count=items;
  if(key=="vit_expand"||key=="vit_qkv_project"||key=="split_mix"||key=="split_expand"||key=="split_contract")index=2;
  else if(key=="vit_project"||key=="split_projection")index=3;
  else if(key=="decoder_project2x"){index=3;count=(*static_cast<unsigned*>(p[6]))*(*static_cast<unsigned*>(p[7]))*(*static_cast<unsigned*>(p[9]));}
  if(index==99)return;if(count>1048576)throw std::runtime_error("WMMA validation scratch capacity");void*reference=*static_cast<void**>(p[index]);p[index]=&scratch;hip.Check(hip.hipMemsetAsync(scratch,0xff,count*4,nullptr),"WMMA sentinel");hip.Check(hip.hipModuleGetFunction(&fn,wmodule,name),name);hip.Check(hip.hipModuleLaunchKernel(fn,(items+255)/256,1,1,32,1,1,0,nullptr,p.data(),nullptr),name);hip.Check(hip.hipDeviceSynchronize(),"WMMA completion");std::vector<float>a(count),b(count);hip.Check(hip.hipMemcpy(a.data(),reference,count*4,2),"reference read");hip.Check(hip.hipMemcpy(b.data(),scratch,count*4,2),"WMMA read");std::string tag=key+"-"+std::to_string(wserial++);save(current+"-wmma-"+tag+".f32",b);save(current+"-reference-"+tag+".f32",a);auto r=compare(a,b);totaldiff+=r.bits;totalinvalid+=r.invalid;printf("WMMA stage=%s count=%u bitdiff=%zu numericdiff=%zu invalid=%zu maxabs=%.9g\n",name,count,r.bits,r.numeric,r.invalid,r.maxabs);report<<"WMMA stage="<<name<<" count="<<count<<" bitdiff="<<r.bits<<" numericdiff="<<r.numeric<<" invalid="<<r.invalid<<" maxabs="<<r.maxabs<<"\n";
 };
 void *sf=nullptr,*sp=nullptr,*dw=nullptr,*dw32=nullptr,*smix=nullptr,*shid=nullptr,*sout=nullptr,*sproj=nullptr,*skip=nullptr,*dout=nullptr;
 if(wmodule){sf=upload(load(L"block23-ffwd.f32",524288));sp=upload(load(L"block23-ffwd-projection.f32",262656));dw=upload(load(L"decoder39-weights.f32",524800));dw32=upload(load(L"block66-weights.f32",2080));smix=alloc(T*512);shid=alloc(T*2048);sout=alloc(T*512);sproj=alloc(T*512);skip=alloc(T*4*512);dout=alloc(T*4*512);}

 for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>input(T*C);for(unsigned i=0;i<input.size();i++)input[i]=pattern?float(int((i*73+19)%2048)-1024)/512.f:fp8(((i*37+11)%96)|((i%3==0)?128:0));std::string base=prefix+"-p"+std::to_string(pattern);save(base+"-input.f32",input);current=base;
  auto*source=buffer(d,input.size()*4,D3D12_HEAP_TYPE_UPLOAD);void*m=nullptr;D3D12_RANGE none{};ck(source->Map(0,&none,&m));memcpy(m,input.data(),input.size()*4);source->Unmap(0,nullptr);std::vector<float>oracle(T*C);
  {NativeVitBlock block;block.Create(d,source,T,ew,cw,qw,pw,dir);for(unsigned stage=0;stage<5;stage++)for(unsigned chunk=0;chunk<block.StageChunks(stage);chunk++){submit.Submit([&](ID3D12GraphicsCommandList*c){block.RecordStageChunk(c,stage,chunk);});submit.Flush();}auto*result=block.Output();auto*rb=buffer(d,oracle.size()*4,D3D12_HEAP_TYPE_READBACK);submit.Submit([&](ID3D12GraphicsCommandList*c){transition(c,result,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_SOURCE);c->CopyBufferRegion(rb,0,result,0,oracle.size()*4);transition(c,result,D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});submit.Flush();D3D12_RANGE range{0,oracle.size()*4};ck(rb->Map(0,&range,&m));memcpy(oracle.data(),m,oracle.size()*4);rb->Unmap(0,&none);rb->Release();}source->Release();save(base+"-d3d-output.f32",oracle);
  hip.Check(hip.hipMemcpy(hi,input.data(),input.size()*4,1),"input upload");for(auto pair:{std::pair<void*,size_t>{hidden,T*E},{contract,T*C},{qkv,T*3*C},{norm,T*3*C},{ex,T*32*T},{inv,T*32},{av,T*C},{out,T*C}})hip.Check(hip.hipMemsetAsync(pair.first,0xff,pair.second*4,nullptr),"sentinel");
  auto dump=[&](const char*stage,void*p,size_t count){std::vector<float>v(count);hip.Check(hip.hipMemcpy(v.data(),p,count*4,2),"HIP stage read");save(base+"-hip-"+stage+".f32",v);size_t invalid=0;for(float f:v)invalid+=!std::isfinite(f);totalinvalid+=invalid;printf("pattern=%u stage=%s count=%zu invalid=%zu\n",pattern,stage,count,invalid);report<<"pattern="<<pattern<<" stage="<<stage<<" count="<<count<<" invalid="<<invalid<<"\n";return v;};
  launch("vit_expand",T*E,{&hi,&he,&hidden,&T,&C,&E});dump("expand",hidden,T*E);
  launch("vit_project",T*C,{&hidden,&hc,&hi,&contract,&T,&E,&C});dump("contract",contract,T*C);
  launch("vit_qkv_project",T*3*C,{&contract,&hq,&qkv,&T});dump("qkv",qkv,T*3*C);
  launch("vit_qkv_normalize",T*96,{&qkv,&hq,&norm,&T});dump("norm",norm,T*3*C);
  launch("vit_attention_scores",T*32*T,{&norm,&ex,&T});dump("ex",ex,T*32*T);
  launch("vit_attention_inverse",T*32,{&ex,&inv,&T});dump("inverse",inv,T*32);
  launch("vit_attention_av",T*C,{&norm,&ex,&inv,&av,&T});dump("av",av,T*C);
  launch("vit_project",T*C,{&av,&hp,&contract,&out,&T,&C,&C});auto actual=dump("output",out,T*C);auto r=compare(oracle,actual);totaldiff+=r.bits;totalinvalid+=r.invalid;printf("pattern=%u stage=ViT64-block31 count=%zu bitdiff=%zu numericdiff=%zu invalid=%zu maxabs=%.9g\n",pattern,actual.size(),r.bits,r.numeric,r.invalid,r.maxabs);report<<"pattern="<<pattern<<" stage=ViT64-block31 count="<<actual.size()<<" bitdiff="<<r.bits<<" numericdiff="<<r.numeric<<" invalid="<<r.invalid<<" maxabs="<<r.maxabs<<"\n";fflush(stdout);
  if(wmodule){unsigned iw=8,ih=8,ow=16,oh=16,ic=1024,oc=512;std::vector<float>skipv(T*4*512);for(size_t i=0;i<skipv.size();i++)skipv[i]=input[(i*13)%input.size()];hip.Check(hip.hipMemcpy(skip,skipv.data(),skipv.size()*4,1),"decoder skip upload");launch("split_mix",T*512,{&hi,&sf,&smix,&T});launch("split_expand",T*2048,{&smix,&sf,&shid,&T});launch("split_contract",T*512,{&shid,&sf,&sout,&T});launch("split_projection",T*512,{&sout,&sp,&hi,&sproj,&T});launch("decoder_project2x",T*oc,{&hi,&dw,&skip,&dout,&iw,&ih,&ow,&oh,&ic,&oc});ow=14;oh=14;launch("decoder_project2x",T*oc,{&hi,&dw,&skip,&dout,&iw,&ih,&ow,&oh,&ic,&oc});ic=64;oc=32;ow=16;oh=16;launch("decoder_project2x",T*oc,{&hi,&dw32,&skip,&dout,&iw,&ih,&ow,&oh,&ic,&oc});}
 }
 hip.Check(hip.hipDeviceSynchronize(),"final sync");for(void*p:allocations)hip.Check(hip.hipFree(p),"free");hip.Check(hip.hipModuleUnload(module),"unload");if(wmodule)hip.Check(hip.hipModuleUnload(wmodule),"WMMA unload");q->Release();d->Release();printf("RESULT bitdiff=%zu invalid=%zu\n",totaldiff,totalinvalid);return totalinvalid?1:totaldiff?3:0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

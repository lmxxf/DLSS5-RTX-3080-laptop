// multihead_fast_validate ASSETS PRODUCTION_FFN_CSO FAST_MODULE OUTPUT_PREFIX [C]
// Original native_c64.hlsl scalar passes, no optimization flags, vs HIP reference.
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

#include "../../src/native_game_submission.h"
#include "../../src/native_c64_shift.h"
extern "C" {__declspec(dllexport) extern const UINT D3D12SDKVersion=721;__declspec(dllexport) const char*D3D12SDKPath=".\\D3D12\\";}
using hip_probe::Handle;
static void ck(HRESULT h){if(FAILED(h))throw std::runtime_error("D3D HRESULT="+std::to_string(unsigned(h)));}
static std::wstring wide(const char*s){int n=MultiByteToWideChar(CP_UTF8,0,s,-1,nullptr,0);std::wstring v(n,L'\0');MultiByteToWideChar(CP_UTF8,0,s,-1,v.data(),n);v.resize(n-1);return v;}
static std::vector<float> read(const std::wstring&p,size_t count){std::ifstream f(p.c_str(),std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(count*4))throw std::runtime_error("weight missing/size");f.seekg(0);std::vector<float>v(count);if(!f.read(reinterpret_cast<char*>(v.data()),count*4))throw std::runtime_error("weight read");return v;}
static void save(const std::string&p,const std::vector<float>&v){std::ofstream f(p,std::ios::binary);if(!f.write(reinterpret_cast<const char*>(v.data()),v.size()*4))throw std::runtime_error("save failed "+p);}
static ID3D12Resource* buffer(ID3D12Device*d,size_t bytes,D3D12_HEAP_TYPE heap,bool uav=false){D3D12_RESOURCE_DESC desc{};desc.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;desc.Width=bytes;desc.Height=1;desc.DepthOrArraySize=desc.MipLevels=1;desc.SampleDesc.Count=1;desc.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;desc.Flags=uav?D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS:D3D12_RESOURCE_FLAG_NONE;D3D12_HEAP_PROPERTIES hp{};hp.Type=heap;ID3D12Resource*r=nullptr;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&desc,heap==D3D12_HEAP_TYPE_UPLOAD?D3D12_RESOURCE_STATE_GENERIC_READ:uav?D3D12_RESOURCE_STATE_UNORDERED_ACCESS:D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&r)));return r;}
static void transition(ID3D12GraphicsCommandList*c,ID3D12Resource*r,D3D12_RESOURCE_STATES a,D3D12_RESOURCE_STATES b){D3D12_RESOURCE_BARRIER v{};v.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;v.Transition={r,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,a,b};c->ResourceBarrier(1,&v);}
static void clear_flags(){wchar_t*env=GetEnvironmentStringsW();std::vector<std::wstring>names;for(auto*p=env;*p;p+=wcslen(p)+1)if(!wcsncmp(p,L"DLSS5_",6)){const wchar_t*e=wcschr(p,L'=');if(e)names.emplace_back(p,size_t(e-p));}FreeEnvironmentStringsW(env);for(auto&n:names)_wputenv((n+L"=").c_str());}
static float fp8(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
struct Comparison {size_t bits{},numeric{},invalid{};double maxabs{};};
static Comparison compare(const std::vector<float>&a,const std::vector<float>&b){if(a.size()!=b.size())throw std::runtime_error("compare size");Comparison r;for(size_t i=0;i<a.size();i++){unsigned x,y;memcpy(&x,&a[i],4);memcpy(&y,&b[i],4);r.bits+=x!=y;r.numeric+=a[i]!=b[i];r.invalid+=!std::isfinite(a[i])||!std::isfinite(b[i]);if(std::isfinite(a[i])&&std::isfinite(b[i]))r.maxabs=std::max(r.maxabs,std::abs(double(a[i])-b[i]));}return r;}
static unsigned char exact8(float v){for(unsigned b=0;b<256;b++)if((b&127)<127&&fp8(b)==v)return static_cast<unsigned char>(b);throw std::runtime_error("nonfinite/non-FP8 matrix operand");}
static void load_flags(const char*path){clear_flags();std::ifstream f(path);if(!f)throw std::runtime_error("flags missing");std::string line;while(std::getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto eq=line.find('=');if(eq==std::string::npos||line.rfind("DLSS5_",0))continue;auto k=line.substr(0,eq),v=line.substr(eq+1);if(_putenv_s(k.c_str(),v.c_str())||_wputenv_s(wide(k.c_str()).c_str(),wide(v.c_str()).c_str()))throw std::runtime_error("set flags");}}
int main(int argc,char**argv){try{
 if(argc!=5&&argc!=7){puts("usage: whole_mh_block_validate ASSETS FLAGS FAST_MODULE PREFIX [WIDTH HEIGHT]");return 2;}load_flags(argv[2]);unsigned W=argc==7?std::stoul(argv[5]):16,H=argc==7?std::stoul(argv[6]):16,C=64,heads=2,T=W*H,windows=T/64,post=4;if(!W||!H||W%8||H%8||static_cast<unsigned long long>(W)*H>1048560)throw std::runtime_error("geometry");auto dir=wide(argv[1]);auto fw=read(dir+L"\\block5-ffn.f32",9*C*C+C),aw=read(dir+L"\\block5-attention.f32",4*C*C+heads*4096+heads+C);std::string prefix=argv[4];std::ofstream report(prefix+"-report.txt");if(!report)throw std::runtime_error("output prefix");{std::ifstream f(argv[2],std::ios::binary);std::ofstream o(prefix+"-flags.txt",std::ios::binary);o<<f.rdbuf();}
 const IID experimental={0x76f5573e,0xf13a,0x40f5,{0xb2,0x97,0x81,0xce,0x9e,0x18,0x93,0x3f}};ck(D3D12EnableExperimentalFeatures(1,&experimental,nullptr,nullptr));IDXGIFactory1*f{};ck(CreateDXGIFactory1(IID_PPV_ARGS(&f)));ID3D12Device*d{};for(unsigned i=0;;i++){IDXGIAdapter1*a{};if(f->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if((desc.VendorId==0x10de||desc.VendorId==0x1002))D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d));a->Release();if(d)break;}f->Release();if(!d)throw std::runtime_error("AMD missing");ID3D12CommandQueue*q{};D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission sub;sub.Create(q,false);
 hip_probe::Api hip;hip.Check(hip.hipInit(0),"init");hip.Check(hip.hipSetDevice(0),"device");Handle module{};hip.Check(hip.hipModuleLoad(&module,argv[3]),"module");std::vector<void*>owned;auto alloc=[&](size_t n){void*p{};hip.Check(hip.hipMalloc(&p,n*4),"alloc");owned.push_back(p);return p;};void*in=alloc(T*C),*hf=alloc(fw.size()),*ha=alloc(aw.size()),*hidden=alloc(T*4*C),*contract=alloc(T*C),*ffn=alloc(T*C),*qkv=alloc(T*3*C),*norm=alloc(T*3*C),*ex=alloc(windows*heads*4096),*prob=alloc(windows*heads*4096),*av=alloc(T*C),*out=alloc(T*C);hip.Check(hip.hipMemcpy(hf,fw.data(),fw.size()*4,1),"FW");hip.Check(hip.hipMemcpy(ha,aw.data(),aw.size()*4,1),"AW");
 auto run=[&](const char*n,unsigned blocks,unsigned threads,std::initializer_list<void*>args){Handle fn{};hip.Check(hip.hipModuleGetFunction(&fn,module,n),n);std::vector<void*>a(args);hip.Check(hip.hipModuleLaunchKernel(fn,blocks,1,1,threads,1,1,0,nullptr,a.data(),nullptr),n);};size_t diff=0,invalid=0;
 for(unsigned pattern=0;pattern<2;pattern++){std::string base=prefix+"-p"+std::to_string(pattern);std::vector<float>input(T*C);for(unsigned i=0;i<input.size();i++)input[i]=fp8(((i*(pattern?53:37)+11)%80)|((i%3==0)?128:0));save(base+"-input.f32",input);auto*source=buffer(d,input.size()*4,D3D12_HEAP_TYPE_UPLOAD);void*m{};D3D12_RANGE none{};ck(source->Map(0,&none,&m));memcpy(m,input.data(),input.size()*4);source->Unmap(0,nullptr);
  std::vector<std::vector<float>> expected(5);const char*names[]={"contract","ffn-projection","normalized","attention-av","final"};
  {NativeMatrixWorkspace workspace;workspace.Create(d,static_cast<UINT64>(T)*C);NativeC64Shift block;
   // Exactly the first C64 block in the900p graph: legal F8 values carried in
   // f32, shift0, nonraw FP8 output, full flags and shared workspace.
   block.Create(d,source,W,H,0,fw,aw,dir,false,C,false,&workspace,false,true,false);
   NativeResidentFlush();
   sub.Submit([&](ID3D12GraphicsCommandList*l){block.Record(l);});sub.Flush();
   if(!workspace.scratch[1]||!workspace.result[0]||!workspace.norm||!workspace.result[1]||!workspace.scratch_readable[1]||!workspace.result_readable[0]||!workspace.norm_readable||!workspace.result_readable[1])throw std::runtime_error("expected900p shared FP8 intermediates were not produced; inspect selected runtime flags");
   ID3D12Resource*resources[]={workspace.scratch[1],workspace.result[0],workspace.norm,workspace.result[1],block.Output()};
   for(unsigned j=0;j<5;j++){size_t count=T*C*(j==2?3:1);auto*rb=buffer(d,count,D3D12_HEAP_TYPE_READBACK);sub.Submit([&](ID3D12GraphicsCommandList*l){transition(l,resources[j],D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_SOURCE);l->CopyBufferRegion(rb,0,resources[j],0,count);transition(l,resources[j],D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});sub.Flush();D3D12_RANGE range{0,count};ck(rb->Map(0,&range,&m));std::vector<unsigned char>raw(count);memcpy(raw.data(),m,count);rb->Unmap(0,&none);rb->Release();{std::ofstream f(base+"-d3d-"+names[j]+".fp8",std::ios::binary);f.write((char*)raw.data(),raw.size());}
    expected[j].resize(count);for(unsigned p=0;p<T;p++)for(unsigned c=0;c<C*(j==2?3:1);c++){size_t dst=p*C*(j==2?3:1)+c,src=dst;if(j==2){unsigned win=p/W/8*(W/8)+(p%W)/8,tok=p/W%8*8+p%8;src=(win*64+tok)*3*C+c;}unsigned b=raw[src];expected[j][dst]=(b&127)==127?std::nanf(""):fp8(b);}save(base+"-d3d-"+names[j]+".f32",expected[j]);
   }
  }source->Release();
  hip.Check(hip.hipMemcpy(in,input.data(),input.size()*4,1),"input upload");for(auto span:{std::pair<void*,size_t>{hidden,T*4*C},{contract,T*C},{ffn,T*C},{qkv,T*3*C},{norm,T*3*C},{ex,windows*heads*4096},{prob,windows*heads*4096},{av,T*C},{out,T*C}})hip.Check(hip.hipMemsetAsync(span.first,0xff,span.second*4,nullptr),"sentinel");
  run("mh_ffn_expand_fast",((T+63)/64)*((4*C+63)/64),512,{&in,&hf,&hidden,&T,&C});run("mh_ffn_contract_fast",((T+63)/64)*((C+63)/64),512,{&hidden,&hf,&contract,&T,&C});run("mh_ffn_project_fast",((T+63)/64)*((C+63)/64),512,{&contract,&in,&hf,&ffn,&T,&C});
  run("mh_qkv_fast",((T+63)/64)*((3*C+63)/64),512,{&ffn,&ha,&qkv,&T,&C});
  // Use the already validated scalar normalize entry to avoid conflating a
  // new wave-normalization experiment with this runtime-selection audit.
  run("mh_qkv_normalize_fast",(T*heads+255)/256,256,{&qkv,&ha,&norm,&T,&C});run("mh_scores_exp_fast",windows*heads*16,32,{&norm,&ha,&ex,&W,&H,&C});run("mh_probabilities_fast",windows*heads*4,32,{&ex,&prob,&windows,&C});run("mh_attention_av_fast",windows*heads*8,32,{&prob,&norm,&av,&W,&H,&C});run("mh_attention_project_fast_matrix",((T+63)/64)*((C+63)/64),512,{&av,&ffn,&ha,&out,&T,&C,&post});hip.Check(hip.hipDeviceSynchronize(),"whole block HIP completion");
  void*actual[]={contract,ffn,norm,av,out};bool first=true;for(unsigned j=0;j<5;j++){std::vector<float>v(expected[j].size());hip.Check(hip.hipMemcpy(v.data(),actual[j],v.size()*4,2),"stage read");save(base+"-hip-"+names[j]+".f32",v);auto r=compare(expected[j],v);diff+=r.bits;invalid+=r.invalid;printf("W=%u H=%u pattern=%u stage=%s bitdiff=%zu numericdiff=%zu invalid=%zu maxabs=%.9g\n",W,H,pattern,names[j],r.bits,r.numeric,r.invalid,r.maxabs);report<<"pattern="<<pattern<<" stage="<<names[j]<<" bitdiff="<<r.bits<<" numericdiff="<<r.numeric<<" invalid="<<r.invalid<<" maxabs="<<r.maxabs<<"\n";if(first&&(r.bits||r.invalid)){printf("FIRST_DIVERGENCE pattern=%u stage=%s\n",pattern,names[j]);report<<"FIRST_DIVERGENCE pattern="<<pattern<<" stage="<<names[j]<<"\n";first=false;}}
  for(auto item:{std::pair<const char*,void*>{"raw-qkv",qkv},{"hidden",hidden}}){size_t n=T*C*(item.second==qkv?3:4);std::vector<float>v(n);hip.Check(hip.hipMemcpy(v.data(),item.second,n*4,2),"diagnostic read");save(base+"-hip-"+item.first+".f32",v);}fflush(stdout);report.flush();
 }
 hip.Check(hip.hipDeviceSynchronize(),"finish");for(auto p:owned)hip.Check(hip.hipFree(p),"free");hip.Check(hip.hipModuleUnload(module),"unload");q->Release();d->Release();printf("RESULT bitdiff=%zu invalid=%zu\n",diff,invalid);return invalid?1:diff?3:0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

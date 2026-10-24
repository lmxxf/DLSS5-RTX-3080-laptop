#define DLSS5_LAYER_BENCH 1
// Matched-input production HLSL vs current HIP layer benchmark.
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
#include "hip_reference_network.h"
#include "../../src/native_c32_stage.h"
#include "../../src/native_split_window.h"
#include "../../src/native_vit_block.h"
#include <chrono>
#include <functional>

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

struct HlslLayerBenchmark {
 static void Describe(NativeVitBlock&v){printf("PATH VIT expand_tiled=%u contract_tiled=%u split_k=%u projection_tiled=%u fused_ffn=%u\n",v.expand.WaveTiled(),v.contract.WaveTiled(),v.contract.SplitK(),v.projection.WaveTiled(),v.fused);}
 static void Describe(NativeC64Shift&s){auto&b=s.body;printf("PATH MH fused_ffn=%u fused_proj0=%u fused_shift=%u fused_qkv_norm=%u attn_fused_qkv=%u fp8_stream=%u\n",b.fused_ffn,b.fused_proj0,b.fused_shift,b.fused_qkv_normalize,b.attn_fused_qkv,b.fp8_stream);}
 static void Describe(NativeC32Stage&s){auto&b=s.body;printf("PATH C32 fused_ffn=%u mapping=%u half_stream=%u\n",b.fused_ffn,b.mapping[0],b.half_stream);}
 static void Raw(NativeC32Stage&s,ID3D12Resource*src){s.body.MapInput(src,3,s.geometry[0],s.geometry[1],s.geometry[4],s.geometry[5],0,0,s.geometry[0]);s.mapped=true;}
};
namespace hip_reference {
struct LayerBenchmark {
 static Tensor Input(Network&n,const std::vector<float>&v){return n.Upload(v.data(),v.size()*4);}
 static Tensor Run(Network&n,Tensor in,U w,U h,U c,U block,U shift,U mode){
  if(c==1024)return n.Vit(in,w*h,block);if(c!=32)return n.Body(in,w,h,c,shift,block,false);
  U sx=(shift&1)?4:0,sy=(shift&2)?4:0,ww=w+2*sx,hh=h+2*sy;
  auto packed=in;if(mode==0){packed=n.New(size_t(ww)*hh*32);n.Run("boundary","hip_c32_pack",size_t(ww)*hh*32,n.P(in),n.P(packed),w,h,ww,hh,sx,sy);}
  std::string fw=block==70?"post70-ffn.f32":n.Block(block,"ffn"),aw=block==70?"post70-attention.f32":n.Block(block,"attention");
  auto raw=n.New(size_t(ww)*hh*16);U windows=ww*hh/64;
  if(mode==2)n.Run("c32_fused_ffn","c32_fast_ffn_attention_fused_half_chain",windows,n.P(in),n.PackedC32Weight(fw,false),n.PackedC32Weight(aw,true),n.P(raw),windows,U(3),U(1),w,h,sx,sy,w,U(0),U(0));
  else if(mode==1)n.Run("c32_fused_ffn","c32_fast_ffn_attention_fused_half_mapped",windows,n.P(in),n.PackedC32Weight(fw,false),n.PackedC32Weight(aw,true),n.P(raw),windows,U(0),U(1),w,h,sx,sy);
  else n.Run("c32_fused_ffn","c32_fast_ffn_attention_fused_half",windows,n.P(packed),n.PackedC32Weight(fw,false),n.PackedC32Weight(aw,true),n.P(raw),windows,U(0),U(1));return raw;
 }
 static void Profile(Network&n,Tensor in,U w,U h,U c,U block,U shift,U mode,const std::vector<float>&expected,std::ostream&csv){
  n.wall_timings.clear();n.opt.wall_profile=true;n.diagnostic_kernel_repeats=20;
  Tensor out;for(unsigned j=0;j<3;j++){out.reset();out=Run(n,in,w,h,c,block,shift,mode);}n.Synchronize();n.opt.wall_profile=false;n.diagnostic_kernel_repeats=1;auto after=Read(n,out,expected.size(),c==32);if(compare(after,expected).bits)throw std::runtime_error("isolated kernel repetition changed output");
  for(auto&entry:n.wall_timings){printf("HIP_KERNEL_BATCH block=%u mode=%u kernel=%s wall_ms=%.6f calls=%.1f\n",block,mode,entry.first.c_str(),entry.second.first/3.,entry.second.second/3.);csv<<block<<','<<c<<','<<mode<<','<<entry.first<<','<<entry.second.first/3.<<','<<entry.second.second/3.<<'\n';}csv.flush();
 }
 static std::vector<float> Read(Network&n,Tensor t,size_t count,bool half){
  std::vector<float>v(count);if(half){std::vector<uint16_t>b(count);n.api.Check(n.api.hipMemcpy(b.data(),t->ptr,count*2,2),"HIP read");for(size_t i=0;i<count;i++)v[i]=Half(b[i]);}
  else n.api.Check(n.api.hipMemcpy(v.data(),t->ptr,count*4,2),"HIP read");return v;
 }
};
}
int main(int argc,char**argv){try{
 if(argc!=5&&argc!=6&&argc!=7&&argc!=8)throw std::runtime_error("usage: compare_layers.exe ASSETS FLAGS MODULES OUTPUT.csv [pattern] [fused-ffn]");
 if(argc==8&&std::string(argv[7])!="mh-only"&&std::string(argv[7])!="c32-only"&&std::string(argv[7])!="c64-only"&&std::string(argv[7])!="all"&&std::string(argv[7])!="vit-only")throw std::runtime_error("unknown layer filter");
 unsigned pattern=argc>=6?std::stoul(argv[5]):0;if(pattern>1)throw std::runtime_error("pattern must be0 or1");
 if(argc>=7&&(std::string(argv[6])!="fused-ffn"&&std::string(argv[6])!="fused-tiled"&&std::string(argv[6])!="fused-selected"))throw std::runtime_error("unknown layer option");load_flags(argv[2]);const unsigned repeats=20;
 const IID experimental={0x76f5573e,0xf13a,0x40f5,{0xb2,0x97,0x81,0xce,0x9e,0x18,0x93,0x3f}};
 ck(D3D12EnableExperimentalFeatures(1,&experimental,nullptr,nullptr));
 IDXGIFactory1*factory{};ck(CreateDXGIFactory1(IID_PPV_ARGS(&factory)));ID3D12Device*d{};
 for(unsigned i=0;;i++){IDXGIAdapter1*a{};if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 info{};a->GetDesc1(&info);if((info.VendorId==0x10de||info.VendorId==0x1002))D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d));a->Release();if(d)break;}factory->Release();if(!d)throw std::runtime_error("AMD missing");
 ID3D12CommandQueue*q{};D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission sub;sub.Create(q,false);
 auto upload=[&](const std::vector<float>&v){auto*u=buffer(d,v.size()*4,D3D12_HEAP_TYPE_UPLOAD);auto*r=buffer(d,v.size()*4,D3D12_HEAP_TYPE_DEFAULT);void*p;D3D12_RANGE none{};ck(u->Map(0,&none,&p));memcpy(p,v.data(),v.size()*4);u->Unmap(0,nullptr);sub.Submit([&](ID3D12GraphicsCommandList*l){l->CopyBufferRegion(r,0,u,0,v.size()*4);transition(l,r,D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});u->Release();return r;};
 auto readback=[&](ID3D12Resource*r,size_t count,unsigned format){size_t bytes=count*format;auto*rb=buffer(d,bytes,D3D12_HEAP_TYPE_READBACK);sub.Submit([&](ID3D12GraphicsCommandList*l){transition(l,r,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_SOURCE);l->CopyBufferRegion(rb,0,r,0,bytes);transition(l,r,D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});void*p;D3D12_RANGE range{0,bytes};ck(rb->Map(0,&range,&p));std::vector<float>v(count);for(size_t i=0;i<count;i++)v[i]=format==1?((static_cast<unsigned char*>(p)[i]&127)==127?std::nanf(""):fp8(static_cast<unsigned char*>(p)[i])):format==2?hip_reference::Half(static_cast<uint16_t*>(p)[i]):static_cast<float*>(p)[i];rb->Unmap(0,nullptr);rb->Release();return v;};
 std::ofstream phases(std::string(argv[4])+".hip-phases.csv");phases<<"block,C,mode,kernel,batch_wall_ms_per_call,calls\n";std::ofstream csv(argv[4]);if(!csv)throw std::runtime_error("CSV open");csv<<"block,C,W,H,shift,mode,round,backend,wall_ms,gpu_ms,bitdiff,invalid,maxabs\n";
 struct Case{unsigned b,c,w,h,shift;};
 for(auto item:{Case{70,32,1600,1024,3},Case{1,32,800,512,0},Case{4,32,800,512,2},Case{5,64,400,256,0},Case{6,64,400,256,3},Case{62,64,400,256,0},Case{63,64,400,256,3},Case{64,64,400,256,1},Case{65,64,400,256,2},Case{9,128,200,128,0},Case{15,256,100,64,0},Case{23,512,50,32,0},Case{31,1024,20,20,0}}){
  auto b=item.b,C=item.c,W=item.w,H=item.h,shift=item.shift;if(argc==8&&((std::string(argv[7])=="mh-only"&&(C==32||C==1024))||(std::string(argv[7])=="c32-only"&&C!=32)||(std::string(argv[7])=="c64-only"&&C!=64)||(std::string(argv[7])=="vit-only"&&C!=1024)))continue;size_t count=size_t(W)*H*C;
  std::string stem=b==70?"post70":"block"+std::to_string(b);
  auto fw=hip_reference::ReadWeights(std::string(argv[1])+"/"+stem+(C==1024?"-expand.f32":C==512?"-ffwd.f32":"-ffn.f32")),aw=hip_reference::ReadWeights(std::string(argv[1])+"/"+stem+(C==1024?"-qkv.f32":"-attention.f32"));
  std::vector<float>input(count);for(size_t i=0;i<count;i++)input[i]=pattern&&C==32?float(int((i*73+19)%2048)-1024)/512.f:fp8(unsigned((i*(pattern?53:37)+i/31+11)%(pattern?96:80))|((i%3==0)?128:0));
  auto*src=upload(input);ID3D12Resource*rawsrc=nullptr;ID3D12Resource*mhsrc=src;const bool decoder64=b>=63&&b<=65;if(decoder64){std::vector<float>packed_input(count/4);auto*bytes=reinterpret_cast<unsigned char*>(packed_input.data());for(size_t i=0;i<count;i++)bytes[i]=exact8(input[i]);mhsrc=upload(packed_input);}
  std::vector<float>bytes;if(C==32){bytes.resize(count/2);auto*half=reinterpret_cast<uint16_t*>(bytes.data());for(unsigned y=0;y<H;y++)for(unsigned x=0;x<W;x++)for(unsigned c=0;c<32;c++){size_t from=(size_t(y)*W+x)*32+c,to=((size_t(y/8)*(W/8)+x/8)*64+(y%8)*8+x%8)*32+c;uint32_t bits;memcpy(&bits,&input[from],4);uint32_t a=bits&0x7fffffffu;half[to]=uint16_t((bits>>16)&0x8000u)|(a?uint16_t((a>>13)-0x1c000u):0);}rawsrc=upload(bytes);}

  hip_reference::Options o;o.assets=argv[1];o.modules=argv[3];o.width=1600;o.height=1024;o.post_shift=3;
  o.wmma=o.wave=o.tiled=o.pooled=o.fast_vit=o.fast_c32=o.fused_c32=o.fused_ffn=o.fast_mh=o.fused_mh=o.mh_wave=o.fast_deep=o.fast_prefix=o.packed_weights=o.packed_c32=o.fp8_normalized=o.fp8_ffn=o.fp8_av=o.fp8_deep=o.fp8_middle=o.half_c32=o.crop_c32=o.fused_qkv_norm=true;
  o.fused_mh_ffn=argc>=7;o.tiled_mh_ffn=argc>=7&&std::string(argv[6])!="fused-ffn";o.tiled_ffn_min_c=argc>=7&&std::string(argv[6])=="fused-selected"?256:64;o.elide_identity_shift=true;
  if(argc==8){if(std::string(argv[6])!="fused-selected")throw std::runtime_error("current MH comparison requires fused-selected");o.fused_ffn_project=true;o.mh_project_crop=true;o.mh_input_mapped=true;o.split_ffn_fused=true;o.split_mix_blocked=true;o.split_project_blocked=true;o.grouped_mh_contract=true;o.ffn_qkv=true;o.ffn_qkv_max_c=256;o.vit_qkv_fused=true;/* production ViT FFN path (native_hip_network.h HIP_FAST): blocked expand/contract, tiled expand weights, packed byte input */o.vit_blocked=o.vit_contract_blocked=true;o.vit_weight_mask=1;o.vit_pack_input=true;o.vit_qkv_blocked=true;o.vit_attn_fused=o.vit_qkv_fp8=o.vit_expand_frag=true;if(const char*v=std::getenv("DLSS5_HIP_VIT_ATTN_FUSED"))o.vit_attn_fused=!strcmp(v,"1");if(const char*v=std::getenv("DLSS5_HIP_VIT_QKV_FP8"))o.vit_qkv_fp8=!strcmp(v,"1");if(const char*v=std::getenv("DLSS5_HIP_VIT_EXPAND_FRAG"))o.vit_expand_frag=!strcmp(v,"1");}
  hip_reference::Network net(o);auto hi=hip_reference::LayerBenchmark::Input(net,input);auto hi_raw=C==32?hip_reference::LayerBenchmark::Input(net,bytes):hip_reference::Tensor{};hip_reference::Tensor ho;
  unsigned current_mode=0;auto hiprun=[&]{ho.reset();ho=hip_reference::LayerBenchmark::Run(net,current_mode==2?hi_raw:hi,W,H,C,b,shift,current_mode);};hiprun();net.Synchronize();
  size_t output_count=C==32?size_t(W+((shift&1)?8:0))*(H+((shift&2)?8:0))*32:count;
  auto actual=hip_reference::LayerBenchmark::Read(net,ho,output_count,C==32);
  for(unsigned mode=0;mode<(C==32?3u:1u);mode++){current_mode=mode;hiprun();net.Synchronize();actual=hip_reference::LayerBenchmark::Read(net,ho,output_count,C==32);
   NativeMatrixWorkspace workspace;std::unique_ptr<NativeC32Stage>c32;std::unique_ptr<NativeC64Shift>mh;std::unique_ptr<NativeSplitWindow>split;std::unique_ptr<NativeVitBlock>vit;std::function<void(ID3D12GraphicsCommandList*)>record;ID3D12Resource*out{};unsigned format;
   if(C==32){c32=std::make_unique<NativeC32Stage>();c32->Create(d,mode==2?rawsrc:src,W,H,shift,fw,aw,wide(argv[1]),true,mode!=0);if(mode==1)c32->MapFromRaster(src);if(mode==2)HlslLayerBenchmark::Raw(*c32,rawsrc);HlslLayerBenchmark::Describe(*c32);c32->SetSkipFinish(true);c32->SetCropNeeded(false);out=c32->RawWork();format=c32->HalfStream()?2:4;record=[&](ID3D12GraphicsCommandList*l){c32->Record(l);};}
   else if(C==1024){vit=std::make_unique<NativeVitBlock>();vit->Create(d,src,W*H,fw,hip_reference::ReadWeights(std::string(argv[1])+"/"+stem+"-contract.f32"),aw,hip_reference::ReadWeights(std::string(argv[1])+"/"+stem+"-projection.f32"),wide(argv[1]));HlslLayerBenchmark::Describe(*vit);out=vit->Output();format=4;record=[&](ID3D12GraphicsCommandList*l){vit->Record(l);};}
   else if(C==512){workspace.Create(d,size_t((W+15)&~7u)*((H+15)&~7u)*C);split=std::make_unique<NativeSplitWindow>();split->Create(d,src,W,H,shift,fw,hip_reference::ReadWeights(std::string(argv[1])+"/"+stem+"-ffwd-projection.f32"),aw,wide(argv[1]),false,&workspace,2);out=split->Output();format=1;record=[&](ID3D12GraphicsCommandList*l){split->Record(l);};}
   else{workspace.Create(d,size_t((W+15)&~7u)*((H+15)&~7u)*C);mh=std::make_unique<NativeC64Shift>();mh->Create(d,mhsrc,W,H,shift,fw,aw,wide(argv[1]),false,C,false,&workspace,decoder64,b!=65,false);HlslLayerBenchmark::Describe(*mh);out=mh->Output();format=b==65?4:1;record=[&](ID3D12GraphicsCommandList*l){mh->Record(l);};}
   NativeResidentFlush();sub.Submit(record);auto expected=readback(out,output_count,format);auto diff=compare(expected,actual);
   printf("CHECK block=%u C=%u mode=%u format=%u bitdiff=%zu invalid=%zu maxabs=%.9g\n",b,C,mode,format,diff.bits,diff.invalid,diff.maxabs);fflush(stdout);if(diff.invalid)throw std::runtime_error("nonfinite layer output");
   NativeNetworkTimestamps timer;timer.Create(d);
   for(unsigned round=0;round<4;round++){bool hip=round==1||round==2;double wall,gpu=-1;
    if(hip){for(unsigned i=0;i<20;i++)hiprun();net.Synchronize();auto start=std::chrono::steady_clock::now();for(unsigned i=0;i<repeats;i++)hiprun();net.Synchronize();wall=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/repeats;}
    else{sub.Submit([&](ID3D12GraphicsCommandList*l){for(unsigned i=0;i<20;i++)record(l);});timer.Reset();auto start=std::chrono::steady_clock::now();sub.Submit([&](ID3D12GraphicsCommandList*l){timer.Mark(l,"begin");for(unsigned i=0;i<repeats;i++)record(l);timer.Mark(l,"end");timer.Resolve(l);});wall=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/repeats;std::vector<double>iv;if(!timer.Intervals(sub.TimestampFrequency(),iv)||iv.size()!=1||!std::isfinite(iv[0])||iv[0]<0)throw std::runtime_error("invalid D3D timing");gpu=iv[0]/repeats;}
    printf("TIME block=%u C=%u W=%u H=%u shift=%u mode=%u round=%u backend=%s wall_ms=%.6f gpu_ms=%.6f\n",b,C,W,H,shift,mode,round,hip?"HIP":"HLSL",wall,gpu);fflush(stdout);
    csv<<b<<','<<C<<','<<W<<','<<H<<','<<shift<<','<<mode<<','<<round<<','<<(hip?"HIP":"HLSL")<<','<<wall<<','<<gpu<<','<<diff.bits<<','<<diff.invalid<<','<<diff.maxabs<<'\n';csv.flush();
   }
   timer.Reset();sub.Submit([&](ID3D12GraphicsCommandList*l){timer.Mark(l,"detail_begin");if(c32)c32->Record(l,&timer,"c32");else if(mh)mh->Record(l,&timer);else if(split)split->Record(l,&timer);else for(unsigned stage=0;stage<5;stage++){vit->RecordStage(l,stage);timer.Mark(l,"vit_stage"+std::to_string(stage));}timer.Mark(l,"detail_end");timer.Resolve(l);});printf("DETAIL block=%u mode=%u backend=HLSL\n",b,mode);timer.Report(sub.TimestampFrequency());hip_reference::LayerBenchmark::Profile(net,mode==2?hi_raw:hi,W,H,C,b,shift,mode,actual,phases);
  }
  net.Synchronize();ho.reset();hi.reset();hi_raw.reset();if(mhsrc!=src)mhsrc->Release();src->Release();if(rawsrc)rawsrc->Release();
 }
 q->Release();d->Release();return 0;
}catch(const std::exception&e){fprintf(stderr,"FAILED: %s\n",e.what());return 1;}}

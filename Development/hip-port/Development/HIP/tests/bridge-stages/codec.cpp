#include <windows.h>
#include <dxgi1_4.h>
#include <type_traits>
#include "native_game_codec.h"
#include "native_game_submission.h"
#include "legacy_codec.h"
#include "full_codec.h"
#include <limits>
static void ck(HRESULT h){if(FAILED(h))throw std::runtime_error("D3D "+std::to_string(unsigned(h)));}
static ID3D12Resource*buf(ID3D12Device*d,UINT64 n,D3D12_HEAP_TYPE type){D3D12_HEAP_PROPERTIES hp{};hp.Type=type;D3D12_RESOURCE_DESC r{};r.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;r.Width=n;r.Height=1;r.DepthOrArraySize=r.MipLevels=1;r.SampleDesc.Count=1;r.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;ID3D12Resource*b{};ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&r,type==D3D12_HEAP_TYPE_UPLOAD?D3D12_RESOURCE_STATE_GENERIC_READ:D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&b)));return b;}
static void bar(ID3D12GraphicsCommandList*c,ID3D12Resource*r,D3D12_RESOURCE_STATES a,D3D12_RESOURCE_STATES b){D3D12_RESOURCE_BARRIER v{};v.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;v.Transition={r,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,a,b};c->ResourceBarrier(1,&v);}
static void same(const std::vector<unsigned char>&a,const std::vector<unsigned char>&b,const char*tag){size_t diff=0;if(a.size()!=b.size())throw std::runtime_error("size mismatch");for(size_t i=0;i<a.size();i++)diff+=a[i]!=b[i];printf("CODEC %s bytes=%zu diff=%zu\n",tag,a.size(),diff);if(diff)throw std::runtime_error("codec differs");}
int wmain(int argc,wchar_t**argv){try{
 if(argc!=5)throw std::runtime_error("old-shaders new-shaders height unorm8");unsigned nh=std::stoul(argv[3]);bool u8=std::stoi(argv[4])!=0;_wputenv_s(L"DLSS5_NETWORK_HEIGHT",argv[3]);_wputenv_s(L"DLSS5_STRENGTH",L"0.25,0.75");_wputenv_s(L"DLSS5_CODEC_SRGB",u8?L"1":L"0");_wputenv_s(L"DLSS5_TEST_FULL_STRENGTH",L"");
 NativeCodecParameters bad;bad.transfer_strength=std::numeric_limits<float>::quiet_NaN();if(bad.Valid())throw std::runtime_error("NaN accepted");bad={};bad.color_strength=2;if(bad.Valid())throw std::runtime_error("range accepted");bad={};bad.debug_view=NativeCodecDebugView(5);if(bad.Valid())throw std::runtime_error("view accepted");
 auto legacy_params=NativeGameCodec::LegacyParameters();if(legacy_params.transfer_strength!=.25f||legacy_params.color_strength!=.75f)throw std::runtime_error("legacy env");
 IDXGIFactory4*f{};ck(CreateDXGIFactory1(IID_PPV_ARGS(&f)));ID3D12Device*d{};for(UINT i=0;;i++){IDXGIAdapter1*a{};if(f->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if(desc.VendorId==0x1002)ck(D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d)));a->Release();if(d)break;}f->Release();if(!d)throw std::runtime_error("AMD missing");
 ID3D12CommandQueue*q{};D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission submit;submit.Create(q,false);
 auto ng=NativeNetworkGeometry::FromHeight(nh);UINT W=nh==1080?1920:640,H=nh==1080?1080:360;ID3D12Resource*in[3]{};
 for(UINT t=0;t<3;t++){
  D3D12_RESOURCE_DESC td{};td.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE2D;td.Width=t==2?W:ng.valid_width;td.Height=t==2?H:ng.valid_height;td.DepthOrArraySize=td.MipLevels=1;td.SampleDesc.Count=1;td.Format=t==2&&u8?DXGI_FORMAT_R8G8B8A8_UNORM:DXGI_FORMAT_R16G16B16A16_FLOAT;
  D3D12_HEAP_PROPERTIES hp{};hp.Type=D3D12_HEAP_TYPE_DEFAULT;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&td,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&in[t])));
  D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};UINT64 n;d->GetCopyableFootprints(&td,0,1,0,&fp,nullptr,nullptr,&n);auto*up=buf(d,n,D3D12_HEAP_TYPE_UPLOAD);void*p{};D3D12_RANGE none{};ck(up->Map(0,&none,&p));std::memset(p,0,n);
  for(UINT y=0;y<td.Height;y++)for(UINT x=0;x<td.Width;x++)for(UINT c=0;c<4;c++){
   auto*row=static_cast<unsigned char*>(p)+fp.Offset+y*fp.Footprint.RowPitch;
   if(t==2&&u8)row[x*4+c]=c==3?255:static_cast<unsigned char>(16+(x+y+c*27)%220);
   else{uint16_t v=c==3?0x3c00:uint16_t((t==2?0x3800:0x3000)+(x*3+y*5+c*11+t*127)%0x0800);std::memcpy(row+x*8+c*2,&v,2);}
  }up->Unmap(0,&none);
  submit.Submit([&](ID3D12GraphicsCommandList*c){D3D12_TEXTURE_COPY_LOCATION from{},to{};from.pResource=up;from.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;from.PlacedFootprint=fp;to.pResource=in[t];to.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;c->CopyTextureRegion(&to,0,0,0,&from,nullptr);bar(c,in[t],D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});up->Release();
 }
 {
 NativeGameCodec codec;LegacyGameCodec legacy;FullGameCodec full;std::vector<ID3D12Resource*>inputs(in,in+3);codec.Create(d,inputs,argv[2]);legacy.Create(d,inputs,argv[1]);full.Create(d,inputs,argv[1]);
 auto capture=[&](auto&stage,const NativeCodecParameters*params,float white){
  auto*output=stage.Output();auto rd=output->GetDesc();bool raw=rd.Dimension==D3D12_RESOURCE_DIMENSION_BUFFER;D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};UINT64 bytes=rd.Width;if(!raw)d->GetCopyableFootprints(&rd,0,1,0,&fp,nullptr,nullptr,&bytes);auto*rb=buf(d,bytes,D3D12_HEAP_TYPE_READBACK);
  submit.Submit([&](ID3D12GraphicsCommandList*c){if constexpr(std::is_same_v<std::decay_t<decltype(stage)>,NativeGameCodec>){if(params)stage.Record(c,std::vector<D3D12_RESOURCE_STATES>(3,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE),white,*params);else stage.Record(c,std::vector<D3D12_RESOURCE_STATES>(3,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE),white);}else stage.Record(c,std::vector<D3D12_RESOURCE_STATES>(3,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE),white);
   bar(c,output,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_SOURCE);if(raw)c->CopyBufferRegion(rb,0,output,0,bytes);else{D3D12_TEXTURE_COPY_LOCATION from{},to{};from.pResource=output;from.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;to.pResource=rb;to.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;to.PlacedFootprint=fp;c->CopyTextureRegion(&to,0,0,0,&from,nullptr);}bar(c,output,D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});
  void*p{};D3D12_RANGE range{0,SIZE_T(bytes)},none{};ck(rb->Map(0,&range,&p));std::vector<unsigned char>v(bytes);std::memcpy(v.data(),p,bytes);rb->Unmap(0,&none);rb->Release();return v;
 };
 NativeCodecParameters normal;
 for(float white:{1.f,.5f,2.f}){same(capture(codec,nullptr,white),capture(legacy,nullptr,white),"legacy-env");same(capture(codec,&normal,white),capture(full,nullptr,white),"explicit-full");}
 auto original=capture(codec,&normal,1);NativeCodecParameters zero{0,0,NativeCodecDebugView::Final};auto identity=capture(codec,&zero,1);if(identity==original)throw std::runtime_error("strength change invisible");
 for(unsigned mode=1;mode<=4;mode++){NativeCodecParameters debug{1,1,NativeCodecDebugView(mode)};auto v=capture(codec,&debug,1);if(v==original)throw std::runtime_error("debug view invisible");if(!u8)for(size_t i=0;i<v.size();i+=2){uint16_t h;std::memcpy(&h,v.data()+i,2);if((h&0x7c00)==0x7c00)throw std::runtime_error("debug nonfinite");}printf("DEBUG view=%u changed=1\n",mode);}
 same(capture(codec,&normal,1),original,"reset-full");same(capture(codec,nullptr,1),capture(legacy,nullptr,1),"legacy-after-override");
 }
 for(auto*p:in)p->Release();q->Release();d->Release();puts("PASS codec parameters");return 0;
}catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

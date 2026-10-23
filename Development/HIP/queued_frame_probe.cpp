#if !defined(DLSS5_USE_HIP) && !defined(DLSS5_COMPARE_HLSL)
#define DLSS5_USE_HIP 1
#endif
// Frozen real HDR capture through the complete persistent NativeGameFrame.
// Input is1296x720 RGBA16F; network900p. This probe never modifies game files.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dxgi1_6.h>
#include <numeric>
#include <algorithm>
#include <cstdio>
#include <cmath>
#include "native_game_frame.h"
#ifndef DLSS5_USE_HIP
extern "C" {__declspec(dllexport) extern const UINT D3D12SDKVersion=721;__declspec(dllexport) const char*D3D12SDKPath=".\\D3D12\\";}
#endif
static void ck(HRESULT hr){if(FAILED(hr))throw std::runtime_error("HRESULT="+std::to_string(unsigned(hr)));}
static ID3D12Resource* buffer(ID3D12Device*d,UINT64 n,D3D12_HEAP_TYPE type){D3D12_HEAP_PROPERTIES hp{};hp.Type=type;D3D12_RESOURCE_DESC r{};r.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;r.Width=n;r.Height=1;r.DepthOrArraySize=r.MipLevels=1;r.SampleDesc.Count=1;r.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;ID3D12Resource*b=nullptr;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&r,type==D3D12_HEAP_TYPE_UPLOAD?D3D12_RESOURCE_STATE_GENERIC_READ:D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&b)));return b;}
static void barrier(ID3D12GraphicsCommandList*c,ID3D12Resource*r,D3D12_RESOURCE_STATES a,D3D12_RESOURCE_STATES b){if(a==b)return;D3D12_RESOURCE_BARRIER x{};x.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;x.Transition={r,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,a,b};c->ResourceBarrier(1,&x);}
static void env(const char*k,const char*v){if(_putenv_s(k,v))throw std::runtime_error("environment update");std::wstring wk(k,k+strlen(k)),wv(v,v+strlen(v));if(_wputenv_s(wk.c_str(),wv.c_str()))throw std::runtime_error("wide environment update");}
static void flags(const wchar_t*path){std::ifstream f(path);if(!f)throw std::runtime_error("flags missing");std::string s;while(std::getline(f,s)){auto p=s.find_first_not_of(" \t\r");if(p==std::string::npos||s[p]=='#'||s[p]==';')continue;s=s.substr(p);auto eq=s.find('=');if(eq==std::string::npos)continue;auto name=s.substr(0,eq),value=s.substr(eq+1);while(!name.empty()&&isspace((unsigned char)name.back()))name.pop_back();while(!value.empty()&&isspace((unsigned char)value.back()))value.pop_back();auto start=value.find_first_not_of(" \t");value=start==std::string::npos?"":value.substr(start);if(name.rfind("DLSS5_",0))continue;env(name.c_str(),value.c_str());}}
static void clear_flags(){wchar_t*all=GetEnvironmentStringsW();std::vector<std::wstring>names;for(auto*p=all;*p;p+=wcslen(p)+1)if(!wcsncmp(p,L"DLSS5_",6)){auto*e=wcschr(p,L'=');if(e)names.emplace_back(p,size_t(e-p));}FreeEnvironmentStringsW(all);for(auto&name:names){std::string n(name.begin(),name.end());env(n.c_str(),"");}}
struct Stats{size_t invalid{},dark{},roi_dark{},roi_count{};double mean{},roi_mean{},min=1e30,max=-1e30;};
static Stats stats(const std::vector<uint16_t>&raw,UINT w,UINT h){Stats s;for(UINT y=0;y<h;y++)for(UINT x=0;x<w;x++){size_t p=(size_t(y)*w+x)*4;float rgb[3];for(unsigned c=0;c<4;c++){float v=NativeHalfToFloat(raw[p+c]);s.invalid+=!std::isfinite(v);if(c<3){rgb[c]=v;if(std::isfinite(v)){s.min=std::min(s.min,double(v));s.max=std::max(s.max,double(v));}}}if(!std::isfinite(rgb[0])||!std::isfinite(rgb[1])||!std::isfinite(rgb[2]))continue;double lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];s.mean+=lum;s.dark+=lum<.01;bool roi=x>=w/4&&x<3*w/4&&y>=h/5&&y<9*h/10;if(roi){s.roi_mean+=lum;s.roi_count++;s.roi_dark+=lum<.01;}}s.mean/=size_t(w)*h;if(s.roi_count)s.roi_mean/=s.roi_count;return s;}
static void save_frame(const std::wstring&prefix,const std::vector<uint16_t>&raw,UINT w,UINT h){FILE*f=_wfopen((prefix+L".f16").c_str(),L"wb");if(!f)throw std::runtime_error("raw output open");bool ok=fwrite(raw.data(),2,raw.size(),f)==raw.size();fclose(f);if(!ok)throw std::runtime_error("raw output write");f=_wfopen((prefix+L".ppm").c_str(),L"wb");if(!f)throw std::runtime_error("PPM open");fprintf(f,"P6\n# Linear RGB clipped to 0..1 for diagnostic preview; raw HDR is in .f16\n%u %u\n255\n",w,h);std::vector<unsigned char>rgb(size_t(w)*h*3);for(size_t p=0;p<size_t(w)*h;p++)for(unsigned c=0;c<3;c++){float v=NativeHalfToFloat(raw[p*4+c]);rgb[p*3+c]=std::isfinite(v)?static_cast<unsigned char>(std::lround(std::max(0.f,std::min(1.f,v))*255.f)):0;}ok=fwrite(rgb.data(),1,rgb.size(),f)==rgb.size();fclose(f);if(!ok)throw std::runtime_error("PPM write");}
int wmain(int argc,wchar_t**argv){try{
 if(argc!=8&&argc!=9&&argc!=10)throw std::runtime_error("usage: queued_frame ASSETS FLAGS MODULES INPUT PREFIX async0|1 rotate0|1|2 [temporal0|1|2|3] [vary-content0|1]");
 unsigned temporal=argc>=9?wcstoul(argv[8],nullptr,10):0;if(temporal>3)throw std::runtime_error("temporal mode");
 bool vary_content=argc==10&&wcstoul(argv[9],nullptr,10)!=0;bool async=wcstoul(argv[6],nullptr,10)!=0;unsigned rotate=wcstoul(argv[7],nullptr,10);if(rotate>2)throw std::runtime_error("rotation mode");
 clear_flags();flags(argv[2]);env("DLSS5_NETWORK_HEIGHT","900");env("DLSS5_HIP_FAST","1");env("DLSS5_TEST_ASYNC_SUBMIT",async?"1":"0");env("DLSS5_GAME_PROBE","0");env("DLSS5_BLACK_PROBE","0");env("DLSS5_SHOW_FPS","0");env("DLSS5_DEBUG_DUMPS","");env("DLSS5_OVERLAP","0");env("DLSS5_HIP_GRAPH","0");
 int len=WideCharToMultiByte(CP_UTF8,0,argv[3],-1,nullptr,0,nullptr,nullptr);std::string mods(len,'\0');WideCharToMultiByte(CP_UTF8,0,argv[3],-1,mods.data(),len,nullptr,nullptr);env("DLSS5_HIP_MODULES",mods.c_str());
 constexpr UINT W=1296,H=720,N=12;size_t count=size_t(W)*H*4;
 std::ifstream f(argv[4],std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(count*2))throw std::runtime_error("capture size");std::vector<uint16_t>pixels(count);f.seekg(0);if(!f.read((char*)pixels.data(),count*2))throw std::runtime_error("capture read");
 IDXGIFactory6*factory{};ck(CreateDXGIFactory2(0,IID_PPV_ARGS(&factory)));ID3D12Device*d{};
 for(UINT i=0;;i++){IDXGIAdapter1*a{};if(factory->EnumAdapterByGpuPreference(i,DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE,IID_PPV_ARGS(&a))==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if((desc.VendorId==0x10de||desc.VendorId==0x1002))D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d));a->Release();if(d)break;}factory->Release();if(!d)throw std::runtime_error("AMD missing");
 ID3D12CommandQueue*q{};D3D12_COMMAND_QUEUE_DESC qd{};ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));NativeGameSubmission submit;submit.Create(q);
 D3D12_HEAP_PROPERTIES hp{};hp.Type=D3D12_HEAP_TYPE_DEFAULT;D3D12_RESOURCE_DESC td{};td.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE2D;td.Width=W;td.Height=H;td.DepthOrArraySize=td.MipLevels=1;td.Format=DXGI_FORMAT_R16G16B16A16_FLOAT;td.SampleDesc.Count=1;
 std::vector<ID3D12Resource*>textures(rotate==2?12:2);for(auto&tex:textures)ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&td,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&tex)));
 D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};UINT64 bytes{};d->GetCopyableFootprints(&td,0,1,0,&fp,nullptr,nullptr,&bytes);
 ID3D12Resource*uploads[2]{},*snapshots[N]{};D3D12_RANGE none{};
 for(UINT j=0;j<2;j++){uploads[j]=buffer(d,bytes,D3D12_HEAP_TYPE_UPLOAD);void*p;ck(uploads[j]->Map(0,&none,&p));memset(p,0,size_t(bytes));for(UINT y=0;y<H;y++){auto*row=(uint16_t*)((char*)p+fp.Offset+y*fp.Footprint.RowPitch);for(UINT x=0;x<W;x++)for(UINT c=0;c<4;c++)row[x*4+c]=pixels[(size_t(y)*W+x)*4+(j&&c<3?2-c:c)];}uploads[j]->Unmap(0,nullptr);}
 for(auto&rb:snapshots)rb=buffer(d,bytes,D3D12_HEAP_TYPE_READBACK);
 auto restore=[&](ID3D12GraphicsCommandList*c,UINT slot,UINT content){D3D12_TEXTURE_COPY_LOCATION dst{},src{};dst.pResource=textures[slot];dst.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;src.pResource=uploads[content];src.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;src.PlacedFootprint=fp;c->CopyTextureRegion(&dst,0,0,0,&src,nullptr);};
 std::vector<ID3D12Resource*>motions(temporal==3?12:2);
 if(temporal){auto md=td;md.Format=DXGI_FORMAT_R16G16_FLOAT;D3D12_PLACED_SUBRESOURCE_FOOTPRINT mf{};UINT64 mb{};d->GetCopyableFootprints(&md,0,1,0,&mf,nullptr,nullptr,&mb);
  for(unsigned j=0;j<motions.size();j++){ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&md,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&motions[j])));auto*u=buffer(d,mb,D3D12_HEAP_TYPE_UPLOAD);void*p;ck(u->Map(0,&none,&p));memset(p,0,size_t(mb));if(j%2)for(UINT y=0;y<H;y++){auto*row=(uint16_t*)((char*)p+mf.Offset+y*mf.Footprint.RowPitch);for(UINT x=0;x<W;x++)row[x*2]=0x1400;}u->Unmap(0,nullptr);
   submit.Submit([&](ID3D12GraphicsCommandList*c){D3D12_TEXTURE_COPY_LOCATION dst{},src{};dst.pResource=motions[j];dst.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;src.pResource=u;src.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;src.PlacedFootprint=mf;c->CopyTextureRegion(&dst,0,0,0,&src,nullptr);barrier(c,motions[j],D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);});submit.Flush();u->Release();
  }
 }
 auto noise=NativeReadF32(std::wstring(argv[1])+L"\\noise.f32","noise");
 std::wstring prefix=argv[5];size_t invalid=0;
 {NativeGameFrame frame;NativeGameFrame::TemporalConfig tc{W,H,W,H};frame.Create(q,textures[0],noise,argv[1],nullptr,temporal?&tc:nullptr);noise.clear();noise.shrink_to_fit();
 auto start=std::chrono::steady_clock::now(),hot_start=start;
 for(UINT i=0;i<N;i++){if(i==2){submit.Submit([](ID3D12GraphicsCommandList*){});submit.Flush();hot_start=std::chrono::steady_clock::now();}UINT slot=rotate==2?i:rotate?i%2:0;
  submit.Submit([&](ID3D12GraphicsCommandList*c){restore(c,slot,vary_content?i%2:slot%2);});
  frame.RebindSourceAfterCompletion(textures[slot]);
  frame.ProcessSubmittedFrame(textures[slot],D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_STATE_COPY_DEST,0,false,temporal?motions[temporal==3?i:temporal==2?i%2:0]:nullptr,!temporal||i==0);
  submit.Submit([&](ID3D12GraphicsCommandList*c){barrier(c,textures[slot],D3D12_RESOURCE_STATE_COPY_DEST,D3D12_RESOURCE_STATE_COPY_SOURCE);D3D12_TEXTURE_COPY_LOCATION dst{},src{};dst.pResource=snapshots[i];dst.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;dst.PlacedFootprint=fp;src.pResource=textures[slot];src.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;c->CopyTextureRegion(&dst,0,0,0,&src,nullptr);barrier(c,textures[slot],D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_COPY_DEST);});
 }
 submit.Submit([](ID3D12GraphicsCommandList*){});submit.Flush();
 printf("batch async=%u rotate=%u frames=%u wall_ms=%.3f\n",async,rotate,N,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());
 printf("hot_ms_per_frame=%.6f\n",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-hot_start).count()/(N-2));
 std::ofstream out((prefix+L".f16").c_str(),std::ios::binary);if(!out)throw std::runtime_error("output");
 for(UINT i=0;i<N;i++){void*p;D3D12_RANGE range{0,size_t(bytes)};ck(snapshots[i]->Map(0,&range,&p));std::vector<uint16_t>raw(count);for(UINT y=0;y<H;y++)memcpy(raw.data()+size_t(y)*W*4,(char*)p+fp.Offset+y*fp.Footprint.RowPitch,size_t(W)*8);snapshots[i]->Unmap(0,&none);auto st=stats(raw,W,H);invalid+=st.invalid;if(!out.write((char*)raw.data(),count*2))throw std::runtime_error("snapshot write");printf("frame=%u luma=%.9g invalid=%zu\n",i,st.mean,st.invalid);}
 }
 for(auto*p:motions)if(p)p->Release();for(auto*p:snapshots)p->Release();for(auto*p:uploads)p->Release();for(auto*p:textures)p->Release();q->Release();d->Release();return invalid?1:0;
}catch(const std::exception&e){fprintf(stderr,"queued probe failed: %s\n",e.what());return 1;}}

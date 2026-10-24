// GPU ordering check without a game or network weights: producer -> deferred FFX copy -> readback.
#define WIN32_LEAN_AND_MEAN
#define NATIVE_BYPASS_TEST 1
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include "../src/native_game_oneshot.h"
void NativeReleaseReservedVram(){}
static NativeGameOneShot neural_oneshot;
struct NativeBypassTestAccess {
 static bool Key(NativeGameOneShot&n,bool down){std::lock_guard<std::mutex>lock(n.request_mutex);n.PollBypassKeyLocked(down);return n.bypass;}
 static void Set(NativeGameOneShot&n,bool bypass){std::lock_guard<std::mutex>lock(n.request_mutex);n.bypass=bypass;n.f6_down=false;n.phase.store(4);}
};
static unsigned ffx_calls=0;
struct Header {uint64_t type;Header*next;};
struct ResourcePayload {void*resource;uint32_t type,format,width,height,depth,mips,flags,usage,state,padding;};
using Dispatch=uint32_t(*)(void**,const Header*);
using ExecuteLists=void(STDMETHODCALLTYPE*)(ID3D12CommandQueue*,UINT,ID3D12CommandList*const*);
static bool ffx_state_to_d3d12(uint32_t s,D3D12_RESOURCE_STATES&out){
 switch(s){case 1:out=D3D12_RESOURCE_STATE_COMMON;return true;case 2:out=D3D12_RESOURCE_STATE_UNORDERED_ACCESS;return true;case 4:out=D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE;return true;case 8:out=D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE;return true;case 12:out=(D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE|D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE);return true;case 16:out=D3D12_RESOURCE_STATE_COPY_SOURCE;return true;case 32:out=D3D12_RESOURCE_STATE_COPY_DEST;return true;default:return false;}
}
static uint32_t CopyFfx(void**,const Header*h){
 ++ffx_calls;
 auto*b=reinterpret_cast<const char*>(h);ID3D12GraphicsCommandList*c;ResourcePayload in,out;
 memcpy(&c,b+16,8);memcpy(&in,b+24,48);memcpy(&out,b+312,48);
 D3D12_RESOURCE_STATES si,so;if(!ffx_state_to_d3d12(in.state,si)||!ffx_state_to_d3d12(out.state,so))return 1;
 D3D12_RESOURCE_BARRIER bars[2]{};for(auto&v:bars)v.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
 bars[0].Transition={static_cast<ID3D12Resource*>(in.resource),D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,si,D3D12_RESOURCE_STATE_COPY_SOURCE};
 bars[1].Transition={static_cast<ID3D12Resource*>(out.resource),D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,so,D3D12_RESOURCE_STATE_COPY_DEST};
 c->ResourceBarrier(2,bars);c->CopyResource(static_cast<ID3D12Resource*>(out.resource),static_cast<ID3D12Resource*>(in.resource));
 for(auto&v:bars)std::swap(v.Transition.StateBefore,v.Transition.StateAfter);c->ResourceBarrier(2,bars);return 0;
}
static Dispatch original=CopyFfx;
#include "../src/native_pre_upscale.h"
static void STDMETHODCALLTYPE ExecuteReal(ID3D12CommandQueue*q,UINT n,ID3D12CommandList*const*ls){q->ExecuteCommandLists(n,ls);}
static void ck(HRESULT h){if(FAILED(h))throw std::runtime_error("HRESULT="+std::to_string(unsigned(h)));}
int main(int argc,char**){try{
 if(!NativeBypassTestAccess::Key(neural_oneshot,true)||!NativeBypassTestAccess::Key(neural_oneshot,true)||!NativeBypassTestAccess::Key(neural_oneshot,false)||NativeBypassTestAccess::Key(neural_oneshot,true)||NativeBypassTestAccess::Key(neural_oneshot,true)||NativeBypassTestAccess::Key(neural_oneshot,false))throw std::runtime_error("F6 edge/held/re-enable mismatch");
 puts("F6_EDGE_TOGGLE_PASS");
 _putenv("DLSS5_PRE_UPSCALE=2");_wputenv(L"DLSS5_PRE_UPSCALE=2");
 _wputenv(argc>1?L"DLSS5_PRE_UPSCALE_ASYNC=1":L"DLSS5_PRE_UPSCALE_ASYNC=0");
 IDXGIFactory4*f=nullptr;ck(CreateDXGIFactory1(IID_PPV_ARGS(&f)));IDXGIAdapter1*a=nullptr;ID3D12Device*d=nullptr;
 for(UINT i=0;f->EnumAdapters1(i,&a)!=DXGI_ERROR_NOT_FOUND;i++){DXGI_ADAPTER_DESC1 desc{};a->GetDesc1(&desc);if(desc.VendorId==0x1002&&SUCCEEDED(D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&d)))){a->Release();break;}a->Release();}f->Release();if(!d)throw std::runtime_error("No AMD D3D12 device");
 D3D12_COMMAND_QUEUE_DESC qd{};ID3D12CommandQueue*q=nullptr;ck(d->CreateCommandQueue(&qd,IID_PPV_ARGS(&q)));
 NativeGameSubmission sync;sync.Create(q,false);
 D3D12_RESOURCE_DESC td{};td.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE2D;td.Width=32;td.Height=32;td.DepthOrArraySize=td.MipLevels=1;td.Format=DXGI_FORMAT_R16G16B16A16_FLOAT;td.SampleDesc.Count=1;td.Flags=D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
 D3D12_HEAP_PROPERTIES hp{};hp.Type=D3D12_HEAP_TYPE_DEFAULT;ID3D12Resource*input=nullptr,*output=nullptr;
 ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&td,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&input)));
 ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&td,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,nullptr,IID_PPV_ARGS(&output)));
 D3D12_RESOURCE_DESC bd{};bd.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;bd.Width=8192;bd.Height=1;bd.DepthOrArraySize=bd.MipLevels=1;bd.SampleDesc.Count=1;bd.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
 ID3D12Resource*upload=nullptr,*readback=nullptr;hp.Type=D3D12_HEAP_TYPE_UPLOAD;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&bd,D3D12_RESOURCE_STATE_GENERIC_READ,nullptr,IID_PPV_ARGS(&upload)));hp.Type=D3D12_HEAP_TYPE_READBACK;ck(d->CreateCommittedResource(&hp,D3D12_HEAP_FLAG_NONE,&bd,D3D12_RESOURCE_STATE_COPY_DEST,nullptr,IID_PPV_ARGS(&readback)));
 ID3D12CommandAllocator*alloc=nullptr;ID3D12GraphicsCommandList*list=nullptr;ck(d->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT,IID_PPV_ARGS(&alloc)));ck(d->CreateCommandList(0,D3D12_COMMAND_LIST_TYPE_DIRECT,alloc,nullptr,IID_PPV_ARGS(&list)));
 for(unsigned frame=0;frame<6;frame++){
  if(frame){ck(alloc->Reset());ck(list->Reset(alloc,nullptr));}
  uint16_t*data;D3D12_RANGE none{};ck(upload->Map(0,&none,reinterpret_cast<void**>(&data)));for(unsigned i=0;i<4096;i++)data[i]=uint16_t(0x3000+frame*512+(i%256));upload->Unmap(0,nullptr);
  D3D12_TEXTURE_COPY_LOCATION dst{},src{};dst.pResource=input;dst.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;src.pResource=upload;src.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;src.PlacedFootprint.Footprint={DXGI_FORMAT_R16G16B16A16_FLOAT,32,32,1,256};
  D3D12_RESOURCE_BARRIER bar{};bar.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;bar.Transition={input,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_DEST};if(frame)list->ResourceBarrier(1,&bar);
  list->CopyTextureRegion(&dst,0,0,0,&src,nullptr);std::swap(bar.Transition.StateBefore,bar.Transition.StateAfter);list->ResourceBarrier(1,&bar);
  alignas(8) unsigned char desc[432]{};Header h{0x10001,nullptr};memcpy(desc,&h,sizeof h);memcpy(desc+16,&list,8);
  ResourcePayload ri{input,2,0,32,32,1,1,0,0,4,0},ro{output,2,0,32,32,1,1,0,0,2,0};memcpy(desc+24,&ri,48);memcpy(desc+72,&ri,48);memcpy(desc+120,&ri,48);memcpy(desc+312,&ro,48);unsigned dims[]={32,32,frame==1?0u:32u,frame==1?0u:32u};memcpy(desc+376,dims,16);
  void*context=reinterpret_cast<void*>(0x1234);
  const bool direct=frame==1||frame==4,late_off=frame==3;
  NativeBypassTestAccess::Set(neural_oneshot,direct);
  _wputenv(direct?L"DLSS5_PRE_UPSCALE=1":L"DLSS5_PRE_UPSCALE=2");
  const auto old_fence=NativePreUpscale::State()?NativePreUpscale::State()->submit.LastValue():0;
  const unsigned old_calls=ffx_calls;
  const bool captured=NativePreUpscale::Capture(&context,reinterpret_cast<Header*>(desc),list,frame+1);
  if(NativePreUpscale::HasPendingJobs()!=captured)throw std::runtime_error("pending publication mismatch");
  if(captured){NativePreUpscale::ObserveWork(list);auto&job=*NativePreUpscale::Jobs().at(list);if(job.following_work!=1)throw std::runtime_error("following work guard skipped");job.following_work=0;}
  if(captured==direct)throw std::runtime_error("capture bypass mismatch");
  if(direct){if(!NativePreUpscale::Jobs().empty())throw std::runtime_error("bypass retained job");if(original(&context,reinterpret_cast<Header*>(desc)))throw std::runtime_error("direct FFX failed");}
  if(late_off){NativeBypassTestAccess::Set(neural_oneshot,true);_wputenv(L"DLSS5_PRE_UPSCALE=1");}
  ck(list->Close());ID3D12CommandList*lists[]={list};const bool intercepted=NativePreUpscale::Execute(q,1,lists,ExecuteReal);
  if(NativePreUpscale::HasPendingJobs())throw std::runtime_error("pending flag retained after execute");
  NativePreUpscale::ObserveWork(nullptr);NativePreUpscale::ObserveBarrier(nullptr,0,nullptr);
  if(intercepted==direct)throw std::runtime_error("execute bypass mismatch");
  if(!intercepted)ExecuteReal(q,1,lists);
  if(ffx_calls!=old_calls+1)throw std::runtime_error("FFX omitted or replayed twice");
  if(direct&&NativePreUpscale::State()&&NativePreUpscale::State()->submit.LastValue()!=old_fence)throw std::runtime_error("bypass submitted private work");
  if(late_off&&NativePreUpscale::State()->low)throw std::runtime_error("late bypass allocated private color");
  printf("route frame=%u direct=%u late_off=%u ffx_calls=1\n",frame,direct,late_off);
  sync.Submit([&](ID3D12GraphicsCommandList*c){D3D12_RESOURCE_BARRIER b{};b.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;b.Transition={output,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE};c->ResourceBarrier(1,&b);auto rdst=src;rdst.pResource=readback;auto rsrc=dst;rsrc.pResource=output;c->CopyTextureRegion(&rdst,0,0,0,&rsrc,nullptr);std::swap(b.Transition.StateBefore,b.Transition.StateAfter);c->ResourceBarrier(1,&b);});
  D3D12_RANGE range{0,8192};ck(readback->Map(0,&range,reinterpret_cast<void**>(&data)));unsigned bad=0;for(unsigned i=0;i<4096;i++)bad+=data[i]!=uint16_t(0x3000+frame*512+(i%256));readback->Unmap(0,&none);printf("frame=%u different=%u\n",frame,bad);if(bad)throw std::runtime_error("GPU order/output mismatch");
 }
 /* 2026-10-03 DLSS5_PRE_UPSCALE=auto, fallback case (the Forza/Wo Long list layout): the first processed job already
    has work after the upscaler dispatch in its list, so auto must fall back to the post-upscale route --
    this frame replays FFX only, the hook goes inert, and a later capture passes the dispatch through direct. */
 _wputenv(L"DLSS5_PRE_UPSCALE=auto");
 NativePreUpscale::AutoDecision().store(0);
 NativeBypassTestAccess::Set(neural_oneshot,false); /* capture must succeed: auto-undecided is mode 1 and a bypassed one-shot would pass through */
 ck(alloc->Reset());ck(list->Reset(alloc,nullptr));
 uint16_t*data2;D3D12_RANGE none2{};ck(upload->Map(0,&none2,reinterpret_cast<void**>(&data2)));for(unsigned i=0;i<4096;i++)data2[i]=uint16_t(0x3000+6*512+(i%256));upload->Unmap(0,nullptr);
 D3D12_TEXTURE_COPY_LOCATION dst2{},src2{};dst2.pResource=input;dst2.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;src2.pResource=upload;src2.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;src2.PlacedFootprint.Footprint={DXGI_FORMAT_R16G16B16A16_FLOAT,32,32,1,256};
 D3D12_RESOURCE_BARRIER bar2{};bar2.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;bar2.Transition={input,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_COPY_DEST};
 list->ResourceBarrier(1,&bar2);list->CopyTextureRegion(&dst2,0,0,0,&src2,nullptr);std::swap(bar2.Transition.StateBefore,bar2.Transition.StateAfter);list->ResourceBarrier(1,&bar2);
 alignas(8) unsigned char desc2[432]{};Header h2{0x10001,nullptr};memcpy(desc2,&h2,sizeof h2);memcpy(desc2+16,&list,8);
 ResourcePayload ri2{input,2,0,32,32,1,1,0,0,4,0},ro2{output,2,0,32,32,1,1,0,0,2,0};memcpy(desc2+24,&ri2,48);memcpy(desc2+72,&ri2,48);memcpy(desc2+120,&ri2,48);memcpy(desc2+312,&ro2,48);unsigned dims2[]={32,32,32,32};memcpy(desc2+376,dims2,16);
 void*context2=reinterpret_cast<void*>(0x5678);
 const unsigned calls_before=ffx_calls;
 if(!NativePreUpscale::Capture(&context2,reinterpret_cast<Header*>(desc2),list,7))throw std::runtime_error("auto did not capture the first job");
 NativePreUpscale::ObserveWork(list); /* a draw after the dispatch in the same list: the pre-upscale contract is violated */
 ck(list->Close());ID3D12CommandList*lists2[]={list};
 if(!NativePreUpscale::Execute(q,1,lists2,ExecuteReal))throw std::runtime_error("auto job not intercepted");
 if(NativePreUpscale::AutoDecision().load()!=2||NativePreUpscale::Mode()!=0||NativePreUpscale::Enabled())throw std::runtime_error("auto did not fall back to the post-upscale route");
 if(ffx_calls!=calls_before+1)throw std::runtime_error("auto fallback frame: FFX omitted or replayed twice");
 sync.Submit([&](ID3D12GraphicsCommandList*c){D3D12_RESOURCE_BARRIER b{};b.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;b.Transition={output,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE};c->ResourceBarrier(1,&b);auto rdst=src2;rdst.pResource=readback;auto rsrc=dst2;rsrc.pResource=output;c->CopyTextureRegion(&rdst,0,0,0,&rsrc,nullptr);std::swap(b.Transition.StateBefore,b.Transition.StateAfter);c->ResourceBarrier(1,&b);});
 D3D12_RANGE range2{0,8192};ck(readback->Map(0,&range2,reinterpret_cast<void**>(&data2)));unsigned bad2=0;for(unsigned i=0;i<4096;i++)bad2+=data2[i]!=uint16_t(0x3000+6*512+(i%256));readback->Unmap(0,&none2);printf("auto fallback frame different=%u\n",bad2);if(bad2)throw std::runtime_error("auto fallback GPU output mismatch");
 /* after the fallback the hook is inert: the next dispatch must pass through untouched (the post route's contract). */
 ck(alloc->Reset());ck(list->Reset(alloc,nullptr));
 if(NativePreUpscale::Capture(&context2,reinterpret_cast<Header*>(desc2),list,8))throw std::runtime_error("hook still capturing after auto fallback");
 if(original(&context2,reinterpret_cast<Header*>(desc2)))throw std::runtime_error("post-fallback direct FFX failed");
 puts("PRE_UPSCALE_AUTO_FALLBACK_SMOKE_PASS");
 puts("PRE_UPSCALE_DEFER_AND_BYPASS_SMOKE_PASS");return 0;
}catch(const std::exception&e){fprintf(stderr,"FAIL: %s\n",e.what());return 1;}}

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <cstdio>
#include "LmxxfNrApi.h"
int wmain(int argc,wchar_t**argv){
 if(argc!=3)return 2;
 auto dll=LoadLibraryW(argv[1]);if(!dll){printf("LOAD_FAILED %lu\n",GetLastError());return 3;}
 auto get=reinterpret_cast<int32_t(*)(uint32_t,LmxxfNrApi*)>(GetProcAddress(dll,"LmxxfNrGetApi"));if(!get)return 4;
 LmxxfNrApi api{};api.struct_size=sizeof(api);int st=get(LMXXF_NR_ABI_VERSION,&api);printf("API status=%d version=%u size=%u\n",st,api.abi_version,api.struct_size);if(st)return 5;
 LmxxfNrCapabilities caps{};caps.struct_size=sizeof(caps);st=api.QueryCapabilities(&caps);printf("CAPS status=%d ABI=%u\n",st,caps.abi_version);if(st)return 6;
 IDXGIFactory4*factory{};if(FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))return 7;
 ID3D12Device*device{};
 for(UINT i=0;;i++){IDXGIAdapter1*a{};if(factory->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 d{};a->GetDesc1(&d);if(d.VendorId==0x10de&&SUCCEEDED(D3D12CreateDevice(a,D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&device)))){printf("NVIDIA adapter selected\n");a->Release();break;}a->Release();}
 factory->Release();if(!device)return 8;D3D12_COMMAND_QUEUE_DESC qd{};qd.Type=D3D12_COMMAND_LIST_TYPE_DIRECT;ID3D12CommandQueue*q{};if(FAILED(device->CreateCommandQueue(&qd,IID_PPV_ARGS(&q))))return 9;
 LmxxfNrCreateInfo ci{};ci.struct_size=sizeof(ci);ci.device=device;ci.queue=q;ci.assets_directory=argv[2];void*ctx{};st=api.Create(&ci,&ctx);
 auto error=[&](){char b[4096]{};api.GetLastError(b,sizeof(b));printf("LAST_ERROR %s\n",b);};printf("CREATE status=%d\n",st);if(st){error();return 10;}
 st=api.PrepareSession(ctx);printf("PREPARE_SESSION status=%d\n",st);if(st){error();return 11;}
 D3D12_HEAP_PROPERTIES heap{};heap.Type=D3D12_HEAP_TYPE_DEFAULT;D3D12_RESOURCE_DESC rd{};rd.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE2D;rd.Width=854;rd.Height=480;rd.DepthOrArraySize=1;rd.MipLevels=1;rd.Format=DXGI_FORMAT_R16G16B16A16_FLOAT;rd.SampleDesc.Count=1;rd.Layout=D3D12_TEXTURE_LAYOUT_UNKNOWN;
 ID3D12Resource*color{};if(FAILED(device->CreateCommittedResource(&heap,D3D12_HEAP_FLAG_NONE,&rd,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,nullptr,IID_PPV_ARGS(&color))))return 12;
 LmxxfNrFrameInfo frame{};frame.struct_size=sizeof(frame);frame.color=color;frame.color_width=854;frame.color_height=480;frame.color_state=D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE;frame.model_scale=1.f;frame.frame_id=1;
 LmxxfNrJob job{};job.struct_size=sizeof(job);st=api.PrepareFrame(ctx,&frame,&job);printf("PREPARE_FRAME status=%d\n",st);error();char status[8192]{};api.GetStatus(ctx,status,sizeof(status));printf("STATUS %s\n",status);
 if(!st){int cancel=api.CancelUnsubmitted(ctx,job.handle);printf("CANCEL status=%d\n",cancel);if(cancel)st=cancel;}
 api.Destroy(ctx);color->Release();q->Release();device->Release();FreeLibrary(dll);return st?13:0;
}

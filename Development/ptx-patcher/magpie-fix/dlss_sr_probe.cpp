#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11.h>
#include <cstdio>
#include <cstdint>
using Init=unsigned(__cdecl*)(const char*,int,const char*,const wchar_t*,ID3D11Device*,unsigned,void*);
using Caps=unsigned(__cdecl*)(void**);
using Create=unsigned(__cdecl*)(ID3D11DeviceContext*,int,void*,void**);
using Release=unsigned(__cdecl*)(void*);
using Shutdown=unsigned(__cdecl*)(ID3D11Device*);
int wmain(int argc,wchar_t**argv){
 setvbuf(stdout,nullptr,_IONBF,0);if(argc!=2)return 2;
 ID3D11Device*d=nullptr;ID3D11DeviceContext*c=nullptr;D3D_FEATURE_LEVEL fl;
 auto hr=D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&d,&fl,&c);
 if(FAILED(hr))return 3;
 auto m=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(!m)return 4;
 auto init=(Init)GetProcAddress(m,"NVSDK_NGX_D3D11_Init_ProjectID");auto caps=(Caps)GetProcAddress(m,"NVSDK_NGX_D3D11_GetCapabilityParameters");auto create=(Create)GetProcAddress(m,"NVSDK_NGX_D3D11_CreateFeature");
 if(!init||!caps||!create){printf("EXPORT_MISSING init=%p caps=%p create=%p\n",init,caps,create);return 5;}
 auto r=init("7c134ab9-9677-4af5-a2b2-bca943350861",0,"Magpie-DLSS-SR-2",L"logs",d,0x15,nullptr);printf("INIT=%08x\n",r);if(r!=1)return 6;
 void*p=nullptr;r=caps(&p);printf("CAPS=%08x\n",r);if(r!=1)return 7;
 auto table=*reinterpret_cast<void***>(p);
 auto u=[&](const char*k,unsigned v){reinterpret_cast<void(__cdecl*)(void*,const char*,unsigned)>(table[4])(p,k,v);};
 auto i=[&](const char*k,int v){reinterpret_cast<void(__cdecl*)(void*,const char*,int)>(table[3])(p,k,v);};
 u("Width",1280);u("Height",720);u("OutWidth",3840);u("OutHeight",2160);i("PerfQualityValue",1);i("RTXValue",0);i("DLSS.Feature.Create.Flags",66);i("DLSS.Enable.Output.Subrects",0);i("DLSS.Hint.Render.Preset.Balanced",10);
 void*h=nullptr;r=create(c,1,p,&h);printf("CREATE_DLSS_SR=%08x handle=%p\n",r,h);
 if(h){auto rel=(Release)GetProcAddress(m,"NVSDK_NGX_D3D11_ReleaseFeature");if(rel)rel(h);}
 auto end=(Shutdown)GetProcAddress(m,"NVSDK_NGX_D3D11_Shutdown1");if(end)end(d);
 return r==1?0:8;
}

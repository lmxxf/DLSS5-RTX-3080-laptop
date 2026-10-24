#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
struct Header { uint64_t type; void* next; };
struct RenderQuery { Header header; uint32_t displayWidth,displayHeight,quality; uint32_t *outWidth,*outHeight; };
using Query=uint32_t(__cdecl*)(void**,Header*);
int wmain(int argc,wchar_t**argv){
 if(argc!=2)return 2;
 auto mod=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
 if(!mod){printf("LOAD_FAIL error=%lu\n",GetLastError());return 3;}
 for(auto name:{"ffxCreateContext","ffxDestroyContext","ffxQuery","ffxDispatch"})
  if(!GetProcAddress(mod,name)){printf("MISSING %s\n",name);return 4;}
 auto query=(Query)GetProcAddress(mod,"ffxQuery");
 for(unsigned quality=1;quality<=4;quality++){
  uint32_t w=0,h=0;RenderQuery q{{0x10003,nullptr},3840,2160,quality,&w,&h};
  auto r=query(nullptr,&q.header);printf("quality=%u result=%u render=%ux%u display=3840x2160\n",quality,r,w,h);
  if(r!=0||!w||!h)return 5;
 }
 return 0;
}

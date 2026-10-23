// Read-only ADL query. Build with AMD display-library include headers.
#include <windows.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "adl_structures.h"
static void* __stdcall allocate(int bytes){return malloc(bytes);}
int main(int argc,char**argv){
 auto dll=LoadLibraryW(L"atiadlxx.dll");if(!dll){fprintf(stderr,"ADL unavailable\n");return 1;}
 auto create=(int(*)(void*(__stdcall*)(int),int,void**))GetProcAddress(dll,"ADL2_Main_Control_Create");
 auto destroy=(int(*)(void*))GetProcAddress(dll,"ADL2_Main_Control_Destroy");
 auto count=(int(*)(void*,int*))GetProcAddress(dll,"ADL2_Adapter_NumberOfAdapters_Get");
 auto info=(int(*)(void*,AdapterInfo*,int))GetProcAddress(dll,"ADL2_Adapter_AdapterInfo_Get");
 auto query=(int(*)(void*,int,ADLPMLogDataOutput*))GetProcAddress(dll,"ADL2_New_QueryPMLogData_Get");
 if(!create||!destroy||!count||!info||!query){fprintf(stderr,"ADL exports missing\n");return 2;}
 void*context=nullptr;if(create(allocate,1,&context)){fprintf(stderr,"ADL init failed\n");return 3;}
 int n=0;if(count(context,&n)||n<=0||n>256)return 4;std::vector<AdapterInfo> adapters(n);for(auto&a:adapters)a.iSize=sizeof(AdapterInfo);if(info(context,adapters.data(),int(n*sizeof(AdapterInfo))))return 5;
 int samples=argc>1?atoi(argv[1]):1;if(samples<1||samples>600)return 6;
 for(int t=0;t<samples;t++){for(auto&a:adapters){ADLPMLogDataOutput data{};data.size=sizeof(data);int status=query(context,a.iAdapterIndex,&data);printf("sample=%d tick=%llu adapter=%d name=%s status=%d",t,GetTickCount64(),a.iAdapterIndex,a.strAdapterName,status);
 if(!status)for(int id:{1,2,8,19,20,23,27}){auto v=data.sensors[id];printf(" sensor%d_supported=%d sensor%d=%d",id,v.supported,id,v.value);}puts("");}fflush(stdout);if(t+1<samples)Sleep(200);}
 destroy(context);FreeLibrary(dll);return 0;
}

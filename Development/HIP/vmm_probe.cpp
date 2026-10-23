// VMM probe: does the Windows HIP 7 runtime export the virtual memory management entry points, and does a sparse mapping
// (reserve 16 MiB of address space, back only [0,4M) and [12M,16M)) actually consume 8 MiB of device memory?
// Build: x86_64-w64-mingw32-g++ -std=c++17 -O2 -static vmm_probe.cpp -o vmm_probe.exe
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <algorithm>
struct MemAllocationProp{unsigned type;unsigned requestedHandleType;struct{unsigned type;int id;}location;void*win32HandleMetaData;struct{unsigned char compressionType,gpuDirectRDMACapable;unsigned short usage;unsigned char reserved[4];}allocFlags;};
struct MemAccessDesc{struct{unsigned type;int id;}location;unsigned flags;};
int main(int argc,char**argv){if(argc>3&&!std::strcmp(argv[1],"tile")){size_t total=strtoull(argv[2],nullptr,10)*1024,chunk=strtoull(argv[3],nullptr,10)*1024;HMODULE dll=LoadLibraryExW(L"amdhip64_7.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
 auto hipInit=(int(*)(unsigned))GetProcAddress(dll,"hipInit");auto reserve=(int(*)(void**,size_t,size_t,void*,unsigned long long))GetProcAddress(dll,"hipMemAddressReserve");auto create=(int(*)(void**,size_t,const MemAllocationProp*,unsigned long long))GetProcAddress(dll,"hipMemCreate");auto map=(int(*)(void*,size_t,size_t,void*,unsigned long long))GetProcAddress(dll,"hipMemMap");auto setaccess=(int(*)(void*,size_t,const MemAccessDesc*,size_t))GetProcAddress(dll,"hipMemSetAccess");auto memcpy_=(int(*)(void*,const void*,size_t,int))GetProcAddress(dll,"hipMemcpy");auto sync=(int(*)())GetProcAddress(dll,"hipDeviceSynchronize");
 hipInit(0);MemAllocationProp prop{};prop.type=1;prop.location.type=1;MemAccessDesc acc{};acc.location.type=1;acc.flags=3;void*base{};int r=reserve(&base,total,65536,nullptr,0);std::printf("tile total=%zu chunk=%zu reserve rc=%d\n",total,chunk,r);
 for(size_t off=0;off<total;off+=chunk){void*h{};r=create(&h,chunk,&prop,0);int m=map((char*)base+off,chunk,0,h,0);int a=setaccess((char*)base+off,chunk,&acc,1);std::printf("chunk@%zu create=%d map=%d access=%d\n",off,r,m,a);if(r||m||a)return 9;}
 std::vector<uint8_t>src(total),dst(total);for(size_t i=0;i<total;i++)src[i]=uint8_t(i*7+3);r=memcpy_(base,src.data(),total,1);int r2=memcpy_(dst.data(),base,total,2);sync();std::printf("data rc=%d/%d equal=%d\n",r,r2,int(dst==src));return 0;}
size_t total_arg=argc>1?strtoull(argv[1],nullptr,10)*1024:0,piece_arg=argc>2?strtoull(argv[2],nullptr,10)*1024:0,off_arg=argc>3?strtoull(argv[3],nullptr,10)*1024:0,piece1_arg=argc>4?strtoull(argv[4],nullptr,10)*1024:0;
 HMODULE dll=LoadLibraryExW(L"amdhip64_7.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!dll){std::printf("no amdhip64_7.dll\n");return 1;}
 const char*names[]={"hipMemAddressReserve","hipMemAddressFree","hipMemCreate","hipMemRelease","hipMemMap","hipMemUnmap","hipMemSetAccess","hipMemGetAllocationGranularity","hipMemGetAccess","hipMemImportFromShareableHandle"};
 bool all=true;for(auto n:names){bool ok=GetProcAddress(dll,n)!=nullptr;std::printf("export %-34s %s\n",n,ok?"yes":"NO");if(!ok&&std::strcmp(n,"hipMemImportFromShareableHandle"))all=false;}
 if(!all){std::printf("vmm unavailable\n");return 2;}
 auto hipInit=(int(*)(unsigned))GetProcAddress(dll,"hipInit");auto hipMemGetInfo=(int(*)(size_t*,size_t*))GetProcAddress(dll,"hipMemGetInfo");
 auto reserve=(int(*)(void**,size_t,size_t,void*,unsigned long long))GetProcAddress(dll,"hipMemAddressReserve");
 auto addrfree=(int(*)(void*,size_t))GetProcAddress(dll,"hipMemAddressFree");
 auto create=(int(*)(void**,size_t,const MemAllocationProp*,unsigned long long))GetProcAddress(dll,"hipMemCreate");
 auto release=(int(*)(void*))GetProcAddress(dll,"hipMemRelease");
 auto map=(int(*)(void*,size_t,size_t,void*,unsigned long long))GetProcAddress(dll,"hipMemMap");
 auto unmap=(int(*)(void*,size_t))GetProcAddress(dll,"hipMemUnmap");
 auto setaccess=(int(*)(void*,size_t,const MemAccessDesc*,size_t))GetProcAddress(dll,"hipMemSetAccess");
 auto granularity=(int(*)(size_t*,const MemAllocationProp*,unsigned))GetProcAddress(dll,"hipMemGetAllocationGranularity");
 auto memset_=(int(*)(void*,int,size_t))GetProcAddress(dll,"hipMemset");auto memcpy_=(int(*)(void*,const void*,size_t,int))GetProcAddress(dll,"hipMemcpy");auto sync=(int(*)())GetProcAddress(dll,"hipDeviceSynchronize");
 int r=hipInit(0);std::printf("hipInit=%d\n",r);
 MemAllocationProp prop{};prop.type=1/*pinned*/;prop.location.type=1/*device*/;prop.location.id=0;
 size_t gmin=0,grec=0;std::printf("granularity min rc=%d",granularity(&gmin,&prop,0));std::printf(" bytes=%zu; recommended rc=%d",gmin,granularity(&grec,&prop,1));std::printf(" bytes=%zu\n",grec);
 size_t g=grec?grec:gmin;if(!g)g=65536;const size_t total=total_arg?total_arg:16u<<20,piece=piece_arg?piece_arg:4u<<20;const size_t piece1=piece1_arg?piece1_arg:piece;const size_t off2=off_arg?off_arg:total-piece;if(piece%g||total%g){std::printf("granularity %zu does not divide 4 MiB pieces\n",g);return 3;}
 for(int pass=0;pass<(argc>1?1:3);pass++){std::printf("-- pass %d\n",pass);
 size_t free0=0,tot=0;hipMemGetInfo(&free0,&tot);
 void*base{};r=reserve(&base,total,g,nullptr,0);std::printf("reserve rc=%d base=%p\n",r,base);if(r)return 4;
 void*h0{},*h1{};r=create(&h0,piece,&prop,0);std::printf("create0 rc=%d\n",r);if(r)return 5;r=create(&h1,piece1,&prop,0);std::printf("create1 rc=%d\n",r);if(r)return 5;
 r=map(base,piece,0,h0,0);std::printf("map0 rc=%d\n",r);if(r)return 6;r=map((char*)base+off2,piece1,0,h1,0);std::printf("map1 rc=%d (offset %zu size %zu)\n",r,off2,piece1);if(r)return 6;
 MemAccessDesc acc{};acc.location.type=1;acc.location.id=0;acc.flags=3;r=setaccess(base,piece,&acc,1);std::printf("access0 rc=%d\n",r);int r1=setaccess((char*)base+off2,piece1,&acc,1);std::printf("access1 rc=%d\n",r1);if(r||r1){std::printf("access failed; skipping the data test\n");unmap(base,piece);unmap((char*)base+off2,piece1);release(h0);release(h1);addrfree(base,total);continue;}
 size_t free1=0;hipMemGetInfo(&free1,&tot);std::printf("device memory consumed by sparse mapping: %.2f MiB (expect ~8)\n",double(free0-free1)/1048576.);
 std::vector<uint8_t>src(piece),dst(piece);for(size_t i=0;i<piece;i++)src[i]=uint8_t(i*7+3);
 r=memcpy_(base,src.data(),piece,1);std::printf("memcpy to [0,4M) rc=%d\n",r);r=memcpy_((char*)base+off2,src.data(),std::min(piece,piece1),1);std::printf("memcpy to [12M,16M) rc=%d\n",r);
 r=memcpy_(dst.data(),(char*)base+off2,std::min(piece,piece1),2);sync();std::printf("readback rc=%d equal=%d\n",r,int(std::equal(dst.begin(),dst.begin()+std::min(piece,piece1),src.begin())));
 r=memset_((char*)base+piece,0,4096);int s=sync();std::printf("memset into the unmapped hole rc=%d sync=%d (any nonzero is the expected fault)\n",r,s);
 unmap(base,piece);unmap((char*)base+off2,piece1);release(h0);release(h1);addrfree(base,total);
 size_t free2=0;hipMemGetInfo(&free2,&tot);std::printf("after teardown delta vs start: %.2f MiB\n",double(free0-free2)/1048576.);}
 return 0;}

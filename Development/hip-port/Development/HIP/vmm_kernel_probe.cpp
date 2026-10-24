// Can a kernel launched through hipModuleLaunchKernel read and write memory that was mapped with the VMM API?
// usage: vmm_kernel_probe.exe copy_probe.hsaco  (build: x86_64-w64-mingw32-g++ -std=c++17 -O2 -static vmm_kernel_probe.cpp -o vmm_kernel_probe.exe)
#include "hip_api.h"
#include <vector>
#include <cstdint>
#include <cstring>
#include <cstdlib>
using namespace hip_probe;
// One physical allocation of `bytes`, mapped in `pieces` equal parts at VA offsets spread over a reservation of `bytes*spread` (holes between parts when spread>1).
static void* SplitHandle(Api&api,size_t bytes,size_t pieces,size_t spread){MemAllocationProp prop{};prop.type=1;prop.location.type=1;MemAccessDesc acc{};acc.location.type=1;acc.flags=3;void*base{};api.Check(api.hipMemAddressReserve(&base,bytes*spread,65536,nullptr,0),"reserve");void*h{};api.Check(api.hipMemCreate(&h,bytes,&prop,0),"create");size_t part=bytes/pieces;
 for(size_t i=0;i<pieces;i++){char*va=static_cast<char*>(base)+i*part*spread;api.Check(api.hipMemMap(va,part,i*part,h,0),"map");api.Check(api.hipMemSetAccess(va,part,&acc,1),"access");}return base;}
static void* Sparse(Api&api,size_t bytes,size_t chunk){MemAllocationProp prop{};prop.type=1;prop.location.type=1;MemAccessDesc acc{};acc.location.type=1;acc.flags=3;void*base{};api.Check(api.hipMemAddressReserve(&base,bytes,chunk,nullptr,0),"reserve");
 for(size_t o=0;o<bytes;o+=chunk){void*h{};api.Check(api.hipMemCreate(&h,chunk,&prop,0),"create");api.Check(api.hipMemMap(static_cast<char*>(base)+o,chunk,0,h,0),"map");api.Check(api.hipMemSetAccess(static_cast<char*>(base)+o,chunk,&acc,1),"access");}return base;}
int main(int argc,char**argv){setvbuf(stdout,nullptr,_IONBF,0);std::printf("start\n");if(argc<2){std::printf("usage: vmm_kernel_probe.exe copy_probe.hsaco\n");return 2;}
 Api api;std::printf("api loaded\n");api.EnableVmm();api.Check(api.hipInit(0),"init");std::printf("init ok\n");Handle m{},fn{};api.Check(api.hipModuleLoad(&m,argv[1]),"module");api.Check(api.hipModuleGetFunction(&fn,m,"copy_probe"),"function");std::printf("module ok\n");
 const unsigned n=1u<<20;const size_t bytes=size_t(n)*4;size_t chunk=argc>2?strtoull(argv[2],nullptr,10)*1024:65536;size_t pieces=argc>3?strtoull(argv[3],nullptr,10):0,spread=argc>4?strtoull(argv[4],nullptr,10):1;void*sparse_in{};std::vector<uint32_t>src(n),got(n);for(unsigned i=0;i<n;i++)src[i]=i*2654435761u;
 auto run=[&](const char*label,void*in,void*out){std::printf("%s: upload",label);size_t up=spread>1?bytes/pieces:bytes;api.Check(api.hipMemcpy(in,src.data(),up,1),"upload");std::printf(" clear");api.Check(api.hipMemsetAsync(out,0,bytes,nullptr),"clear");std::printf(" launch");unsigned count=spread>1?unsigned(n/pieces):n;void*args[]={&in,&out,&count};api.Check(api.hipModuleLaunchKernel(fn,n/256,1,1,256,1,1,0,nullptr,args,nullptr),"launch");std::printf(" sync");api.Check(api.hipDeviceSynchronize(),"sync");std::printf(" readback");api.Check(api.hipMemcpy(got.data(),out,bytes,2),"readback");size_t bad=0;for(unsigned i=0;i<count;i++)if(got[i]!=src[i]+1u)bad++;std::printf("\n%-44s mismatches=%zu first_out=%08x expect=%08x\n",label,bad,got[0],src[0]+1u);};
 void*dense_in{},*dense_out{};api.Check(api.hipMalloc(&dense_in,bytes),"malloc");api.Check(api.hipMalloc(&dense_out,bytes),"malloc");
 
 if(pieces){std::printf("one handle, %zu pieces, spread %zu\n",pieces,spread);sparse_in=SplitHandle(api,bytes,pieces,spread);}else{std::printf("mapping sparse buffer chunk=%zu\n",chunk);sparse_in=Sparse(api,bytes,chunk);}std::printf("mapped\n");
 run("dense in -> dense out (control)",dense_in,dense_out);
 run("VMM in -> dense out",sparse_in,dense_out);
 return 0;}

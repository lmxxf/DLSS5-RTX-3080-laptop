// Dynamic HIP validation host; no HIP SDK headers or import library.
#include "hip_api.h"
#include <vector>
#include <random>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <fstream>
#include <limits>
using namespace hip_probe;
using U8=unsigned char; using U16=unsigned short; using U32=unsigned;
static U32 bits(float v){U32 b;std::memcpy(&b,&v,4);return b;}
static float decode(U8 x){const unsigned a=x&127,e=a>>3,m=a&7;double v=e?std::ldexp(1.0+m/8.0,int(e)-7):m/512.0;return float(x&128?-v:v);}
static U8 quant(float v){if(v==0)return std::signbit(v)?128:0;unsigned best=0;double err=1e100;for(unsigned i=0;i<127;i++){double d=std::abs(std::abs(double(v))-decode(U8(i)));if(d<err||(d==err&&!(i&1))){best=i;err=d;}}return U8(best|(std::signbit(v)?128:0));}
static U16 half_rne(float f){U32 b=bits(f),s=(b>>16)&0x8000,a=b&0x7fffffff;if(a>=0x7f800000)return U16(s|0x7c00|(a>0x7f800000?0x200:0));int e=int(a>>23)-127;U32 m=(a&0x7fffff)|0x800000;if(e>15)return U16(s|0x7c00);if(e<-25)return U16(s);unsigned shift=e<-14?unsigned(-e-1):13;U32 q=m>>shift,r=m&((1u<<shift)-1),h=1u<<(shift-1);q+=(r>h||(r==h&&(q&1)));if(e<-14)return U16(s|q);return U16(s|((e+14)<<10)+q);}
template<class T>static void save(const std::string&path,const std::vector<T>&v){std::ofstream f(path,std::ios::binary);if(!f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T)))throw std::runtime_error("write "+path);}
struct Case{std::vector<U8>a=std::vector<U8>(512),b=std::vector<U8>(512);std::vector<float>c=std::vector<float>(256);std::string name;bool exact{};};
struct Result{std::vector<float>d,mid;std::vector<U16>half;std::vector<U32>status;};
int main(int argc,char**argv){try{
 if(argc<3||argc>5){fprintf(stderr,"usage: wmma_validate MODULE OUTPUT_PREFIX [HIP_MAJOR=7] [DEVICE=0]\n");return 2;}
 Api api(argc>3?unsigned(std::stoul(argv[3])):7);api.Check(api.hipInit(0),"init");int count=0;api.Check(api.hipGetDeviceCount(&count),"count");int device=argc>4?std::stoi(argv[4]):0;if(device<0||device>=count)throw std::runtime_error("device out of range");api.Check(api.hipSetDevice(device),"set device");char name[256]{};api.Check(api.hipDeviceGetName(name,256,device),"device name");int version=0;api.Check(api.hipRuntimeGetVersion(&version),"version");printf("device=%s runtime=%d module=%s\n",name,version,argv[1]);
 std::vector<Case>cases;auto add=[&](const char*n,bool exact)->Case&{cases.emplace_back();cases.back().name=n;cases.back().exact=exact;return cases.back();};
 add("zero",true);{auto&t=add("carry_C",true);for(unsigned i=0;i<256;i++)t.c[i]=int(i%31)-15;}
 {auto&t=add("ones",true);std::fill(t.a.begin(),t.a.end(),quant(1));std::fill(t.b.begin(),t.b.end(),quant(1));}
 // Exercise both K16 chunks, all 16 A rows and all 16 B columns at each k.
 for(unsigned k=0;k<32;k++){auto&t=add("basis_k",true);t.name+=std::to_string(k);for(unsigned m=0;m<16;m++)t.a[m*32+k]=quant(float(int(m%7)-3));for(unsigned n=0;n<16;n++)t.b[k*16+n]=quant(float(int(n%9)-4));}
 std::mt19937 rng(1201);for(unsigned j=0;j<16;j++){auto&t=add("random_integer",true);for(auto&v:t.a)v=quant(float(int(rng()%9)-4));for(auto&v:t.b)v=quant(float(int(rng()%9)-4));for(auto&v:t.c)v=float(int(rng()%9)-4);}
 for(unsigned j=0;j<24;j++){auto&t=add(j<12?"random_moderate":"random_fullfinite",false);auto next=[&](){unsigned mag=j<12?(rng()%81):(rng()%127);return U8(mag|((rng()&1)<<7));};for(auto&v:t.a)v=next();for(auto&v:t.b)v=next();for(auto&v:t.c)v=decode(next());}
 const U8 boundary[]={0,128,1,129,7,135,8,136,0x38,0xb8,0x7e,0xfe};
 for(unsigned j=0;j<4;j++){auto&t=add("boundary_cancel",false);for(unsigned i=0;i<512;i++){t.a[i]=boundary[(i+j)%12];t.b[i]=boundary[(i*7+j)%12];}if(j==3)for(auto&v:t.c)v=16777216.0f;}
 U32 n=U32(cases.size());std::vector<U8>a,b;std::vector<float>c;for(auto&t:cases){a.insert(a.end(),t.a.begin(),t.a.end());b.insert(b.end(),t.b.begin(),t.b.end());c.insert(c.end(),t.c.begin(),t.c.end());}std::string prefix=argv[2];save(prefix+"-a.fp8",a);save(prefix+"-b.fp8",b);save(prefix+"-c.f32",c);std::ofstream manifest(prefix+"-cases.txt");for(unsigned i=0;i<n;i++)manifest<<i<<" "<<cases[i].name<<" exact="<<cases[i].exact<<"\n";
 Handle module{};api.Check(api.hipModuleLoad(&module,argv[1]),"module load");std::vector<void*>allocations;auto alloc=[&](size_t bytes){void*p{};api.Check(api.hipMalloc(&p,bytes),"malloc");allocations.push_back(p);return p;};void*da=alloc(a.size()),*db=alloc(b.size()),*dc=alloc(c.size()*4),*dd=alloc(c.size()*4),*dm=alloc(c.size()*4),*dh=alloc(c.size()*2),*ds=alloc(n*4);api.Check(api.hipMemcpy(da,a.data(),a.size(),1),"A upload");api.Check(api.hipMemcpy(db,b.data(),b.size(),1),"B upload");api.Check(api.hipMemcpy(dc,c.data(),c.size()*4,1),"C upload");
 auto run=[&](const char*entry,const char*tag){Handle fn{};api.Check(api.hipModuleGetFunction(&fn,module,entry),"get function");for(auto p:{dd,dm})api.Check(api.hipMemsetAsync(p,0xff,c.size()*4,nullptr),"sentinel");api.Check(api.hipMemsetAsync(dh,0xff,c.size()*2,nullptr),"half sentinel");api.Check(api.hipMemsetAsync(ds,0xff,n*4,nullptr),"status sentinel");void*args[]={&da,&db,&dc,&dd,&dm,&dh,&ds,&n};api.Check(api.hipModuleLaunchKernel(fn,n,1,1,32,1,1,0,nullptr,args,nullptr),"WMMA launch");api.Check(api.hipDeviceSynchronize(),"WMMA completion");Result r;r.d.resize(c.size());r.mid.resize(c.size());r.half.resize(c.size());r.status.resize(n);api.Check(api.hipMemcpy(r.d.data(),dd,c.size()*4,2),"D read");api.Check(api.hipMemcpy(r.mid.data(),dm,c.size()*4,2),"partial read");api.Check(api.hipMemcpy(r.half.data(),dh,c.size()*2,2),"half read");api.Check(api.hipMemcpy(r.status.data(),ds,n*4,2),"status read");save(prefix+tag+"-d.f32",r.d);save(prefix+tag+"-partial.f32",r.mid);save(prefix+tag+"-d.f16",r.half);return r;};
 auto fp8=run("dlss5_wmma_fp8_k32","-fp8"),fp16=run("dlss5_wmma_f16_k32","-f16");size_t failures=0,bitdiff=0,zerodiff=0,halfdiff=0;double maxerr=0,maxdiff=0;std::ofstream report(prefix+"-report.txt");
 for(unsigned j=0;j<n;j++){size_t bad=0,diff=0;for(auto status:{fp8.status[j],fp16.status[j]})bad+=status!=0;
 for(unsigned m=0;m<16;m++)for(unsigned col=0;col<16;col++){unsigned idx=j*256+m*16+col;double ref=cases[j].c[m*16+col],sumabs=std::abs(ref);for(unsigned k=0;k<32;k++){double v=double(decode(cases[j].a[m*32+k]))*decode(cases[j].b[k*16+col]);ref+=v;sumabs+=std::abs(v);if(k==15||k==31){double tolerance=cases[j].exact?0:64*std::ldexp(1.,-24)*sumabs+std::ldexp(1.,-149);for(const Result*r:{&fp8,&fp16}){float got=k==15?r->mid[idx]:r->d[idx];double error=std::abs(double(got)-ref);maxerr=std::max(maxerr,error);bad+=!std::isfinite(got)||error>tolerance;}}}
 for(const Result*r:{&fp8,&fp16})bad+=r->half[idx]!=half_rne(r->d[idx]);for(unsigned stage=0;stage<2;stage++){float x=stage?fp8.d[idx]:fp8.mid[idx],y=stage?fp16.d[idx]:fp16.mid[idx];if(bits(x)!=bits(y)){if(x==0&&y==0)zerodiff++;else{bitdiff++;diff++;}}maxdiff=std::max(maxdiff,std::abs(double(x)-y));}halfdiff+=fp8.half[idx]!=fp16.half[idx];}
 failures+=bad;report<<j<<" "<<cases[j].name<<" failures="<<bad<<" fp8_f16_bitdiff="<<diff<<"\n";if(bad||diff)printf("case=%u %s failures=%zu bitdiff=%zu\n",j,cases[j].name.c_str(),bad,diff);
 }
 printf("RESULT cases=%u failures=%zu fp8_f16_bitdiff=%zu signed_zero_diff=%zu half_diff=%zu max_cpu_abs_error=%.9g max_fp8_f16_abs_diff=%.9g\n",n,failures,bitdiff,zerodiff,halfdiff,maxerr,maxdiff);report<<"failures="<<failures<<" bitdiff="<<bitdiff<<" signed_zero_diff="<<zerodiff<<" half_diff="<<halfdiff<<" max_cpu_abs_error="<<maxerr<<" max_fp8_f16_abs_diff="<<maxdiff<<"\n";
 api.Check(api.hipDeviceSynchronize(),"final fence");for(void*p:allocations)api.Check(api.hipFree(p),"free");api.Check(api.hipModuleUnload(module),"unload");if(failures)return 1;if(bitdiff||halfdiff)return 3;return 0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

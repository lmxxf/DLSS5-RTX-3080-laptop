// Isolated operator differentials: each WMMA stage consumes the same inputs as scalar.
#include "hip_api.h"
#include <vector>
#include <fstream>
#include <cstring>
#include <cmath>
#include <algorithm>
using namespace hip_probe;
using U=unsigned;
static float fp8(U b){U e=(b>>3)&15,m=b&7;float v=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-v:v;}
static std::vector<float>read(const std::string&p,size_t n){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=std::streamoff(n*4))throw std::runtime_error("input size/missing: "+p);std::vector<float>v(n);f.seekg(0);if(!f.read((char*)v.data(),n*4))throw std::runtime_error("read");return v;}
static void save(const std::string&p,const std::vector<float>&v){std::ofstream f(p,std::ios::binary);if(!f.write((const char*)v.data(),v.size()*4))throw std::runtime_error("save "+p);}
static void lattice(const std::vector<float>&v,size_t n,const char*label){static const std::vector<float>values=[](){std::vector<float>a;for(U b=0;b<256;b++)if((b&127)<127)a.push_back(fp8(b));std::sort(a.begin(),a.end());return a;}();for(size_t i=0;i<n;i++)if(!std::isfinite(v[i])||!std::binary_search(values.begin(),values.end(),v[i]))throw std::runtime_error(std::string(label)+" not finite exact E4M3 at "+std::to_string(i));}
int main(int argc,char**argv){try{
 if(argc<5||argc>7){puts("usage: multihead_tiled_validate ASSETS SCALAR_MODULE TILED_MODULE OUTPUT_PREFIX [C=64|128|256|512|32] [OPTIONAL_NAIVE_WMMA_MODULE]");return 2;}U C=argc>=6?U(std::stoul(argv[5])):64;if(C!=32&&C!=64&&C!=128&&C!=256&&C!=512)throw std::runtime_error("channels");std::string dir=argv[1],prefix=argv[4];std::ofstream report(prefix+"-report.txt");if(!report)throw std::runtime_error("output directory");
 U first=C==64?5:C==128?9:C==256?15:23,dsblock=C==32?4:C==64?8:C==128?14:22,heads=C/32;std::vector<float>fw,aw;bool mlp=C>=64&&C<=256,attention=C!=32;
 if(mlp){fw=read(dir+"/block"+std::to_string(first)+"-ffn.f32",9*C*C+C);lattice(fw,9*C*C,"FFN matrix weights");}
 if(attention){aw=read(dir+"/block"+std::to_string(first)+"-attention.f32",4*C*C+heads*4096+heads+C);lattice(aw,4*C*C,"attention matrix weights");}
 auto dw=read(dir+(C==512?"/head-matrix.f32":"/block"+std::to_string(dsblock)+"-ds.f32"),2*C*C);lattice(dw,dw.size(),"pool matrix weights");
 Api hip;hip.Check(hip.hipInit(0),"init");hip.Check(hip.hipSetDevice(0),"device");Handle scalar{},wmma{};hip.Check(hip.hipModuleLoad(&scalar,argv[2]),"scalar module");hip.Check(hip.hipModuleLoad(&wmma,argv[3]),"TILED module");Handle naive{};if(argc==7)hip.Check(hip.hipModuleLoad(&naive,argv[6]),"naive module");
 using EventCreate=int(*)(Handle*);using EventRecord=int(*)(Handle,Handle);using EventSync=int(*)(Handle);using EventElapsed=int(*)(float*,Handle,Handle);using EventDestroy=int(*)(Handle);
 EventCreate ec{};EventRecord er{};EventSync es{};EventElapsed ee{};EventDestroy ed{};if(naive){hip.Load(ec,"hipEventCreate");hip.Load(er,"hipEventRecord");hip.Load(es,"hipEventSynchronize");hip.Load(ee,"hipEventElapsedTime");hip.Load(ed,"hipEventDestroy");}
 std::string last_name;std::vector<void*>last_args;U last_groups{};U W=20,H=W,T=W*H,windows=T/64,raw=1,PW=W/2,PH=H/2,PT=PW*PH,zero=0;std::vector<void*>allocated;
 auto alloc=[&](size_t n){void*p{};hip.Check(hip.hipMalloc(&p,n*4),"alloc");allocated.push_back(p);return p;};auto upload=[&](const std::vector<float>&v){if(v.empty())return (void*)nullptr;void*p=alloc(v.size());hip.Check(hip.hipMemcpy(p,v.data(),v.size()*4,1),"weights upload");return p;};void*hf=upload(fw),*ha=upload(aw),*hd=upload(dw),*in=alloc(T*C),*hidden=alloc(T*4*C),*middle=alloc(T*C),*ffn=alloc(T*C),*qkv=alloc(T*3*C),*norm=alloc(T*2*C),*ex=alloc(windows*heads*4096),*prob=alloc(windows*heads*4096),*av=alloc(T*C),*out=alloc(T*C),*pooled=alloc(PT*C),*down=alloc(PT*2*C),*candidate=alloc(std::max(T*4*C,windows*heads*4096));
 auto get=[&](void*p,size_t n){std::vector<float>v(n);hip.Check(hip.hipMemcpy(v.data(),p,n*4,2),"readback");return v;};
 auto run=[&](Handle module,const char*name,U groups,U threads,std::initializer_list<void*>args){Handle fn{};hip.Check(hip.hipModuleGetFunction(&fn,module,name),name);std::vector<void*>p(args);if(module==wmma){last_name=name;last_args=p;last_groups=groups;}hip.Check(hip.hipModuleLaunchKernel(fn,groups,1,1,threads,1,1,0,nullptr,p.data(),nullptr),name);};
 size_t diff=0,invalid=0;
 for(U pattern=0;pattern<2;pattern++){std::string base=prefix+"-p"+std::to_string(pattern);std::vector<float>input(T*C);for(U i=0;i<input.size();i++)input[i]=fp8(((i*(pattern?53:37)+(pattern?29:11))%80)|((i%(pattern?5:3)==0)?128:0));lattice(input,input.size(),"input");save(base+"-input.f32",input);hip.Check(hip.hipMemcpy(in,input.data(),input.size()*4,1),"input upload");
 auto check=[&](const char*tag,void*reference,U count){hip.Check(hip.hipDeviceSynchronize(),"stage completion");auto a=get(reference,count),b=get(candidate,count);save(base+"-scalar-"+tag+".f32",a);save(base+"-tiled-"+tag+".f32",b);size_t nd=0,ni=0;double mx=0;for(U i=0;i<count;i++){U x,y;memcpy(&x,&a[i],4);memcpy(&y,&b[i],4);nd+=x!=y;ni+=!std::isfinite(a[i])||!std::isfinite(b[i]);if(std::isfinite(a[i])&&std::isfinite(b[i]))mx=std::max(mx,std::abs(double(a[i])-b[i]));}diff+=nd;invalid+=ni;printf("C=%u pattern=%u stage=%s count=%u bitdiff=%zu invalid=%zu maxabs=%.9g\n",C,pattern,tag,count,nd,ni,mx);report<<"C="<<C<<" pattern="<<pattern<<" stage="<<tag<<" count="<<count<<" bitdiff="<<nd<<" invalid="<<ni<<" maxabs="<<mx<<"\n";if(naive){U cols=last_name=="mh_ffn_expand_tiled"?4*C:last_name=="mh_qkv_tiled"?3*C:last_name=="mh_pool_project_tiled"?2*C:C;U rows=count/cols;std::string nn=last_name.substr(0,last_name.size()-6)+"_wmma";
 auto bench=[&](Handle mod,const std::string&entry,U grid,U threads){Handle fn{},a{},b{};hip.Check(hip.hipModuleGetFunction(&fn,mod,entry.c_str()),"bench function");auto dispatch=[&](){hip.Check(hip.hipModuleLaunchKernel(fn,grid,1,1,threads,1,1,0,nullptr,last_args.data(),nullptr),"bench launch");};for(int j=0;j<3;j++)dispatch();hip.Check(ec(&a),"event create");hip.Check(ec(&b),"event create");hip.Check(er(a,nullptr),"record begin");for(int j=0;j<10;j++)dispatch();hip.Check(er(b,nullptr),"record end");hip.Check(es(b),"event sync");float ms=0;hip.Check(ee(&ms,a,b),"elapsed");hip.Check(ed(a),"event destroy");hip.Check(ed(b),"event destroy");return ms/10;};
 float oldms=bench(naive,nn,((rows+15)/16)*(cols/16),32),newms=bench(wmma,last_name,last_groups,512);printf("TIMING stage=%s M=%u N=%u naive_ms=%.6f tiled_ms=%.6f speedup=%.3f\n",tag,rows,cols,oldms,newms,oldms/newms);report<<"TIMING stage="<<tag<<" naive_ms="<<oldms<<" tiled_ms="<<newms<<" speedup="<<oldms/newms<<"\n";
 }fflush(stdout);report.flush();};
 auto sentinel=[&](U n){hip.Check(hip.hipMemsetAsync(candidate,0xff,n*4,nullptr),"sentinel");};
 auto validate_input=[&](void*p,U count,const char*tag){hip.Check(hip.hipDeviceSynchronize(),"lattice sync");auto v=get(p,count);lattice(v,v.size(),tag);};
 if(mlp){sentinel(T*4*C);run(scalar,"mh_ffn_expand",(T*4*C+255)/256,256,{&in,&hf,&hidden,&T,&C});run(wmma,"mh_ffn_expand_tiled",((T+63)/64)*((4*C+63)/64),512,{&in,&hf,&candidate,&T,&C});check("expand",hidden,T*4*C);validate_input(hidden,T*4*C,"hidden");
 sentinel(T*C);run(scalar,"mh_ffn_contract",(T*C+255)/256,256,{&hidden,&hf,&middle,&T,&C});run(wmma,"mh_ffn_contract_tiled",((T+63)/64)*((C+63)/64),512,{&hidden,&hf,&candidate,&T,&C});check("contract",middle,T*C);validate_input(middle,T*C,"middle");
 sentinel(T*C);run(scalar,"mh_ffn_project",(T*C+255)/256,256,{&middle,&in,&hf,&ffn,&T,&C});run(wmma,"mh_ffn_project_tiled",((T+63)/64)*((C+63)/64),512,{&middle,&in,&hf,&candidate,&T,&C});check("ffn-project",ffn,T*C);
 }else hip.Check(hip.hipMemcpy(ffn,input.data(),input.size()*4,1),"attention input");
 if(attention){validate_input(ffn,T*C,"FFN/output to QKV");sentinel(T*3*C);run(scalar,"mh_qkv",(T*3*C+255)/256,256,{&ffn,&ha,&qkv,&T,&C});run(wmma,"mh_qkv_tiled",((T+63)/64)*((3*C+63)/64),512,{&ffn,&ha,&candidate,&T,&C});check("qkv",qkv,T*3*C);
 // Independent attention projection: same exact lattice AV on both backends.
 hip.Check(hip.hipMemcpy(av,input.data(),input.size()*4,1),"isolated AV input");
 sentinel(T*C);run(scalar,"mh_attention_project",(T*C+255)/256,256,{&av,&ffn,&ha,&out,&T,&C,&raw});run(wmma,"mh_attention_project_tiled",((T+63)/64)*((C+63)/64),512,{&av,&ffn,&ha,&candidate,&T,&C,&raw});check("attention-project",out,T*C);
 }else hip.Check(hip.hipMemcpy(out,input.data(),input.size()*4,1),"pool input");
 run(scalar,"mh_pool",(PT*C+255)/256,256,{&out,&pooled,&PW,&PH,&W,&zero,&zero,&C});validate_input(pooled,PT*C,"pooled");sentinel(PT*2*C);run(scalar,"mh_pool_project",(PT*2*C+255)/256,256,{&pooled,&hd,&down,&PW,&PH,&zero,&zero,&C});run(wmma,"mh_pool_project_tiled",((PT+63)/64)*((2*C+63)/64),512,{&pooled,&hd,&candidate,&PW,&PH,&zero,&zero,&C});check("pool-project",down,PT*2*C);
 }

 // M400,N32: half of the tiled output columns are invalid. Small integers
 // make all arithmetic exact, so this test does not depend on a CPU reduction order.
 {U M=400,N=32,K=64,skip=~0u,raw_probe=1;std::vector<float>x(M*K),w(N*K),ref(M*N);
  for(U i=0;i<x.size();i++)x[i]=float(int((i*7+3)%7)-3);
  for(U i=0;i<w.size();i++)w[i]=float(int((i*13+1)%5)-2);
  for(U m=0;m<M;m++)for(U n=0;n<N;n++){float z=0;for(U k=0;k<K;k++)z+=x[m*K+k]*w[n*K+k];ref[m*N+n]=z;}
  void*dx=upload(x),*dw=upload(w),*dr=alloc(M*N+256);hip.Check(hip.hipMemsetAsync(dr,0xff,(M*N+256)*4,nullptr),"tail probe sentinel");
  run(wmma,"mh_dense_tiled_probe",((M+63)/64)*((N+63)/64),512,{&dx,&dx,&dw,&dr,&M,&N,&K,&skip,&raw_probe});hip.Check(hip.hipDeviceSynchronize(),"tail probe completion");auto got=get(dr,M*N+256);size_t bad=0;for(U i=0;i<M*N;i++)bad+=got[i]!=ref[i];for(U i=M*N;i<M*N+256;i++){U b;memcpy(&b,&got[i],4);bad+=b!=0xffffffffu;}diff+=bad;printf("tail_probe M400 N32 K64 failures=%zu\n",bad);report<<"tail_probe M400 N32 K64 failures="<<bad<<"\n";
 }
 hip.Check(hip.hipDeviceSynchronize(),"final sync");for(auto*p:allocated)hip.Check(hip.hipFree(p),"free");if(naive)hip.Check(hip.hipModuleUnload(naive),"unload naive");hip.Check(hip.hipModuleUnload(wmma),"unload WMMA");hip.Check(hip.hipModuleUnload(scalar),"unload scalar");printf("RESULT bitdiff=%zu invalid=%zu\n",diff,invalid);return invalid?1:diff?3:0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

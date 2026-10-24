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
 if(argc<5||argc>6){puts("usage: multihead_wmma_validate ASSETS SCALAR_MODULE WMMA_MODULE OUTPUT_PREFIX [C=64|128|256|512|32]");return 2;}U C=argc==6?U(std::stoul(argv[5])):64;if(C!=32&&C!=64&&C!=128&&C!=256&&C!=512)throw std::runtime_error("channels");std::string dir=argv[1],prefix=argv[4];std::ofstream report(prefix+"-report.txt");if(!report)throw std::runtime_error("output directory");
 U first=C==64?5:C==128?9:C==256?15:23,dsblock=C==32?4:C==64?8:C==128?14:22,heads=C/32;std::vector<float>fw,aw;bool mlp=C>=64&&C<=256,attention=C!=32;
 if(mlp){fw=read(dir+"/block"+std::to_string(first)+"-ffn.f32",9*C*C+C);lattice(fw,9*C*C,"FFN matrix weights");}
 if(attention){aw=read(dir+"/block"+std::to_string(first)+"-attention.f32",4*C*C+heads*4096+heads+C);lattice(aw,4*C*C,"attention matrix weights");}
 auto dw=read(dir+(C==512?"/head-matrix.f32":"/block"+std::to_string(dsblock)+"-ds.f32"),2*C*C);lattice(dw,dw.size(),"pool matrix weights");
 Api hip;hip.Check(hip.hipInit(0),"init");hip.Check(hip.hipSetDevice(0),"device");Handle scalar{},wmma{};hip.Check(hip.hipModuleLoad(&scalar,argv[2]),"scalar module");hip.Check(hip.hipModuleLoad(&wmma,argv[3]),"WMMA module");U W=C==512?8:16,H=W,T=W*H,windows=T/64,raw=1,PW=W/2,PH=H/2,PT=PW*PH,zero=0;std::vector<void*>allocated;
 auto alloc=[&](size_t n){void*p{};hip.Check(hip.hipMalloc(&p,n*4),"alloc");allocated.push_back(p);return p;};auto upload=[&](const std::vector<float>&v){if(v.empty())return (void*)nullptr;void*p=alloc(v.size());hip.Check(hip.hipMemcpy(p,v.data(),v.size()*4,1),"weights upload");return p;};void*hf=upload(fw),*ha=upload(aw),*hd=upload(dw),*in=alloc(T*C),*hidden=alloc(T*4*C),*middle=alloc(T*C),*ffn=alloc(T*C),*qkv=alloc(T*3*C),*norm=alloc(T*2*C),*ex=alloc(windows*heads*4096),*prob=alloc(windows*heads*4096),*av=alloc(T*C),*out=alloc(T*C),*pooled=alloc(PT*C),*down=alloc(PT*2*C),*candidate=alloc(std::max(T*4*C,windows*heads*4096));
 auto get=[&](void*p,size_t n){std::vector<float>v(n);hip.Check(hip.hipMemcpy(v.data(),p,n*4,2),"readback");return v;};
 auto run=[&](Handle module,const char*name,U groups,U threads,std::initializer_list<void*>args){Handle fn{};hip.Check(hip.hipModuleGetFunction(&fn,module,name),name);std::vector<void*>p(args);hip.Check(hip.hipModuleLaunchKernel(fn,groups,1,1,threads,1,1,0,nullptr,p.data(),nullptr),name);};
 size_t diff=0,invalid=0;
 for(U pattern=0;pattern<2;pattern++){std::string base=prefix+"-p"+std::to_string(pattern);std::vector<float>input(T*C);for(U i=0;i<input.size();i++)input[i]=fp8(((i*(pattern?53:37)+(pattern?29:11))%80)|((i%(pattern?5:3)==0)?128:0));lattice(input,input.size(),"input");save(base+"-input.f32",input);hip.Check(hip.hipMemcpy(in,input.data(),input.size()*4,1),"input upload");
 auto check=[&](const char*tag,void*reference,U count){hip.Check(hip.hipDeviceSynchronize(),"stage completion");auto a=get(reference,count),b=get(candidate,count);save(base+"-scalar-"+tag+".f32",a);save(base+"-wmma-"+tag+".f32",b);size_t nd=0,ni=0;double mx=0;for(U i=0;i<count;i++){U x,y;memcpy(&x,&a[i],4);memcpy(&y,&b[i],4);nd+=x!=y;ni+=!std::isfinite(a[i])||!std::isfinite(b[i]);if(std::isfinite(a[i])&&std::isfinite(b[i]))mx=std::max(mx,std::abs(double(a[i])-b[i]));}diff+=nd;invalid+=ni;printf("C=%u pattern=%u stage=%s count=%u bitdiff=%zu invalid=%zu maxabs=%.9g\n",C,pattern,tag,count,nd,ni,mx);report<<"C="<<C<<" pattern="<<pattern<<" stage="<<tag<<" count="<<count<<" bitdiff="<<nd<<" invalid="<<ni<<" maxabs="<<mx<<"\n";fflush(stdout);report.flush();};
 auto sentinel=[&](U n){hip.Check(hip.hipMemsetAsync(candidate,0xff,n*4,nullptr),"sentinel");};
 auto validate_input=[&](void*p,U count,const char*tag){hip.Check(hip.hipDeviceSynchronize(),"lattice sync");auto v=get(p,count);lattice(v,v.size(),tag);};
 if(mlp){sentinel(T*4*C);run(scalar,"mh_ffn_expand",(T*4*C+255)/256,256,{&in,&hf,&hidden,&T,&C});run(wmma,"mh_ffn_expand_wmma",((T+15)/16)*(4*C/16),32,{&in,&hf,&candidate,&T,&C});check("expand",hidden,T*4*C);validate_input(hidden,T*4*C,"hidden");
 sentinel(T*C);run(scalar,"mh_ffn_contract",(T*C+255)/256,256,{&hidden,&hf,&middle,&T,&C});run(wmma,"mh_ffn_contract_wmma",((T+15)/16)*(C/16),32,{&hidden,&hf,&candidate,&T,&C});check("contract",middle,T*C);validate_input(middle,T*C,"middle");
 sentinel(T*C);run(scalar,"mh_ffn_project",(T*C+255)/256,256,{&middle,&in,&hf,&ffn,&T,&C});run(wmma,"mh_ffn_project_wmma",((T+15)/16)*(C/16),32,{&middle,&in,&hf,&candidate,&T,&C});check("ffn-project",ffn,T*C);
 }else hip.Check(hip.hipMemcpy(ffn,input.data(),input.size()*4,1),"attention input");
 if(attention){validate_input(ffn,T*C,"FFN/output to QKV");sentinel(T*3*C);run(scalar,"mh_qkv",(T*3*C+255)/256,256,{&ffn,&ha,&qkv,&T,&C});run(wmma,"mh_qkv_wmma",((T+15)/16)*(3*C/16),32,{&ffn,&ha,&candidate,&T,&C});check("qkv",qkv,T*3*C);
 run(scalar,"mh_normalize",(T*heads+255)/256,256,{&qkv,&ha,&norm,&T,&C});validate_input(norm,T*2*C,"normalized QK");sentinel(windows*heads*4096);run(scalar,"mh_scores_exp",windows*heads*16,256,{&norm,&ha,&ex,&W,&H,&C});run(wmma,"mh_scores_exp_wmma",windows*heads*16,32,{&norm,&ha,&candidate,&W,&H,&C});check("scores-exp",ex,windows*heads*4096);
 run(scalar,"mh_probabilities",(windows*heads*64+255)/256,256,{&ex,&prob,&windows,&C});validate_input(prob,windows*heads*4096,"probabilities");sentinel(T*C);run(scalar,"mh_attention_av",(T*C+255)/256,256,{&prob,&qkv,&av,&W,&H,&C});run(wmma,"mh_attention_av_wmma",windows*heads*8,32,{&prob,&qkv,&candidate,&W,&H,&C});check("av",av,T*C);validate_input(av,T*C,"AV");
 sentinel(T*C);run(scalar,"mh_attention_project",(T*C+255)/256,256,{&av,&ffn,&ha,&out,&T,&C,&raw});run(wmma,"mh_attention_project_wmma",((T+15)/16)*(C/16),32,{&av,&ffn,&ha,&candidate,&T,&C,&raw});check("attention-project",out,T*C);
 }else hip.Check(hip.hipMemcpy(out,input.data(),input.size()*4,1),"pool input");
 run(scalar,"mh_pool",(PT*C+255)/256,256,{&out,&pooled,&PW,&PH,&W,&zero,&zero,&C});validate_input(pooled,PT*C,"pooled");sentinel(PT*2*C);run(scalar,"mh_pool_project",(PT*2*C+255)/256,256,{&pooled,&hd,&down,&PW,&PH,&zero,&zero,&C});run(wmma,"mh_pool_project_wmma",((PT+15)/16)*(2*C/16),32,{&pooled,&hd,&candidate,&PW,&PH,&zero,&zero,&C});check("pool-project",down,PT*2*C);
 }
 hip.Check(hip.hipDeviceSynchronize(),"final sync");for(auto*p:allocated)hip.Check(hip.hipFree(p),"free");hip.Check(hip.hipModuleUnload(wmma),"unload WMMA");hip.Check(hip.hipModuleUnload(scalar),"unload scalar");printf("RESULT bitdiff=%zu invalid=%zu\n",diff,invalid);return invalid?1:diff?3:0;
 }catch(const std::exception&e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}}

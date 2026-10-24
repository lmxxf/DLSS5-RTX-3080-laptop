// vit_project_frag and vit_qkv_project_normalize_fused_f16compact_fp8_frag (fragment-tile weights) against the production
// kernels: real block 31/38 weights, synthetic lattice av / H-rounded contract inputs, 400 and 640 tokens; outputs bitwise.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 for(U block:{31u,38u})for(U tokens:{400u,640u})for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>av(size_t(tokens)*1024),skip(av.size()),in(av.size());
  for(size_t i=0;i<av.size();i++){unsigned code=pattern?unsigned((i*41+i/23+7)%110):unsigned((i*29+i/13+3)%90);if(i%5==0)code|=128;av[i]=fp8v(code);skip[i]=fp8v(unsigned((i*17+i/7+1)%100)|((i%3)?0:128));float x=float(int((i*73+i/11)%4001)-2000)/512.f;uint32_t b;std::memcpy(&b,&x,4);b&=0xffffe000u;std::memcpy(&x,&b,4);in[i]=x;}
  auto a=n.Upload(av.data(),av.size()*4),s=n.Upload(skip.data(),skip.size()*4),c=n.Upload(in.data(),in.size()*4);
  auto o1=n.New(av.size()),o2=n.New(av.size()),q1=n.New(size_t(tokens)*768),q2=n.New(size_t(tokens)*768);
  std::vector<unsigned char>hid(size_t(tokens)*4096);for(size_t i=0;i<hid.size();i++){unsigned code=unsigned((i*31+i/19+pattern*3)%112);if(i%7==0)code|=128;hid[i]=(unsigned char)code;}auto hb=n.Upload(hid.data(),hid.size()),c1=n.New(av.size()),c2=n.New(av.size());
  n.Run("deep","vit_contract_blocked_fp8",size_t(tokens)*1024,n.P(hb),n.PackedVitWeight(n.Block(block,"contract"),1024,4096,false),n.P(s),n.P(c1),tokens,U(4096),U(1024));
  n.Run("deep","vit_contract_blocked_fp8_frag",size_t(tokens)*1024,n.P(hb),n.PackedVitWeight(n.Block(block,"contract"),1024,4096,true,true),n.P(s),n.P(c2),tokens,U(4096),U(1024));
  n.Run("deep","vit_project",size_t(tokens)*1024,n.P(a),n.PackedDeepWeight(n.Block(block,"projection"),1048576),n.P(s),n.P(o1),tokens,U(1024),U(1024));
  n.Run("deep","vit_project_frag",size_t(tokens)*1024,n.P(a),n.PackedVitProjectionFrag(n.Block(block,"projection")),n.P(s),n.P(o2),tokens,U(1024),U(1024));
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8",size_t(tokens)*3072,n.P(c),n.PackedVitQkvWeight(n.Block(block,"qkv")),n.P(q1),tokens);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8_frag",size_t(tokens)*3072,n.P(c),n.PackedVitQkvWeightFrag(n.Block(block,"qkv")),n.P(q2),tokens);n.Synchronize();
  std::vector<float>x(av.size()),y(av.size());std::vector<unsigned char>u(size_t(tokens)*3072),v(u.size());
  n.api.Check(n.api.hipMemcpy(x.data(),n.P(o1),x.size()*4,2),"proj ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(o2),y.size()*4,2),"proj frag");n.api.Check(n.api.hipMemcpy(u.data(),n.P(q1),u.size(),2),"qkv ref");n.api.Check(n.api.hipMemcpy(v.data(),n.P(q2),v.size(),2),"qkv frag");
  std::vector<float>cx(av.size()),cy(av.size());n.api.Check(n.api.hipMemcpy(cx.data(),n.P(c1),cx.size()*4,2),"contract ref");n.api.Check(n.api.hipMemcpy(cy.data(),n.P(c2),cy.size()*4,2),"contract frag");size_t cd=0;for(size_t i=0;i<cx.size();i++)cd+=memcmp(&cx[i],&cy[i],4)!=0;
  size_t pd=0,qd=0,bad=0;for(size_t i=0;i<x.size();i++){pd+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}for(size_t i=0;i<u.size();i++){qd+=u[i]!=v[i];bad+=((u[i]&127)==127)||((v[i]&127)==127);}
  printf("block=%u tokens=%u pattern=%u proj_bitdiff=%zu qkv_bytediff=%zu contract_bitdiff=%zu invalid=%zu\n",block,tokens,pattern,pd,qd,cd,bad);ok=ok&&!pd&&!qd&&!cd&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_vit_linear_frag ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_deep=o.fast_vit=o.packed_weights=o.fp8_deep=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"vit linear frag matches\n":"vit linear frag MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

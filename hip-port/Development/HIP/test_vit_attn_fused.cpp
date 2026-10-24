// Bit-exactness of vit_attention_fused against the three-kernel path (scores_fast / inverse_fast / av_fast).
// Synthetic normalized Q/K/V on the E4M3 lattice (what vit_qkv_project_normalize_fused_* emits), three token counts
// (720p 240, 900p 400, 1080p 640) and two value patterns. Compares the attention output bytes; any difference fails.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 for(unsigned tokens:{240u,400u,640u})for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>v(size_t(3)*tokens*1024);
  for(size_t i=0;i<v.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%96):unsigned((i*37+i/17+5)%80);if(i%3==0)code|=128;v[i]=fp8(code);}
  auto in=n.Upload(v.data(),v.size()*4);
  auto ex=n.New(size_t(tokens)*32*tokens),inv=n.New(size_t(tokens)*32),a=n.New(size_t(tokens)*1024),b=n.New(size_t(tokens)*1024);
  n.Run("deep","vit_attention_scores_fast",size_t(tokens)*32*tokens,n.P(in),n.P(ex),tokens);
  n.Run("deep","vit_attention_inverse_fast",size_t(tokens)*32,n.P(ex),n.P(inv),tokens);
  n.Run("deep","vit_attention_av_fast",size_t(tokens)*1024,n.P(in),n.P(ex),n.P(inv),n.P(a),tokens);
  n.Run("deep",tokens<=256?"vit_attention_fused_256":tokens<=400?"vit_attention_fused_400":"vit_attention_fused_640",size_t(tokens)*512,n.P(in),n.P(b),tokens);n.Synchronize();
  std::vector<float>x(size_t(tokens)*1024),y(x.size());
  n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),x.size()*4,2),"read reference");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),y.size()*4,2),"read fused");
  size_t diff=0,bad=0;float maxabs=0;for(size_t i=0;i<x.size();i++){diff+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);maxabs=std::fmax(maxabs,std::fabs(x[i]-y[i]));}
  printf("tokens=%u pattern=%u bitdiff=%zu invalid=%zu maxabs=%.9g\n",tokens,pattern,diff,bad,maxabs);ok=ok&&!diff&&!bad;
  /* byte QKV edge: real block31 QKV weights on a lattice contract input; the byte store must decode to the f32 store
     bit for bit (sign of zero included), and the bytein attention must reproduce the f32-input fused attention. */
  std::vector<float>c(size_t(tokens)*1024);for(size_t i=0;i<c.size();i++){unsigned code=pattern?unsigned((i*41+i/23+7)%96):unsigned((i*29+i/13+3)%80);if(i%5==0)code|=128;c[i]=fp8(code);}
  auto cin=n.Upload(c.data(),c.size()*4);auto qw=n.PackedVitQkvWeight(n.Block(31,"qkv"));
  auto nf=n.New(size_t(tokens)*3072),n8=n.New(size_t(tokens)*768),af=n.New(size_t(tokens)*1024),a8=n.New(size_t(tokens)*1024);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact",size_t(tokens)*3072,n.P(cin),qw,n.P(nf),tokens);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8",size_t(tokens)*3072,n.P(cin),qw,n.P(n8),tokens);
  std::string fused=tokens<=256?"vit_attention_fused_256":tokens<=400?"vit_attention_fused_400":"vit_attention_fused_640";
  n.Run("deep",fused.c_str(),size_t(tokens)*512,n.P(nf),n.P(af),tokens);
  n.Run("deep",(fused+"_bytein").c_str(),size_t(tokens)*512,n.P(n8),n.P(a8),tokens);n.Synchronize();
  std::vector<float>vf(size_t(tokens)*3072),oa(size_t(tokens)*1024),ob(oa.size());std::vector<unsigned char>v8(vf.size());
  n.api.Check(n.api.hipMemcpy(vf.data(),n.P(nf),vf.size()*4,2),"read f32 qkv");n.api.Check(n.api.hipMemcpy(v8.data(),n.P(n8),v8.size(),2),"read byte qkv");
  n.api.Check(n.api.hipMemcpy(oa.data(),n.P(af),oa.size()*4,2),"read f32 attention");n.api.Check(n.api.hipMemcpy(ob.data(),n.P(a8),ob.size()*4,2),"read byte attention");
  size_t qdiff=0,qbad=0,adiff=0,abad=0;for(size_t i=0;i<vf.size();i++){float d=fp8(v8[i]);qdiff+=memcmp(&d,&vf[i],4)!=0;qbad+=!std::isfinite(vf[i]);}
  for(size_t i=0;i<oa.size();i++){adiff+=memcmp(&oa[i],&ob[i],4)!=0;abad+=!std::isfinite(oa[i])||!std::isfinite(ob[i]);}
  printf("tokens=%u pattern=%u qkv_bytediff=%zu qkv_invalid=%zu bytein_attention_bitdiff=%zu invalid=%zu\n",tokens,pattern,qdiff,qbad,adiff,abad);ok=ok&&!qdiff&&!qbad&&!adiff&&!abad;
  /* expand M4 (four token tiles per wave) against the single-tile tiled byte-input expand: real block31 expand weights,
     packed lattice input; hidden bytes must be identical, including the partial last token group. */
  auto ew=n.PackedVitWeight(n.Block(31,"expand"),4096,1024,true);auto packed=n.New(size_t(tokens)*256),h1=n.New(size_t(tokens)*1024),h4=n.New(size_t(tokens)*1024);
  n.Run("deep","vit_pack_input",size_t(tokens)*256,n.P(cin),n.P(packed),U(tokens*1024));
  n.Run("deep","vit_expand_blocked_fp8_tiled_bytein",size_t(tokens)*4096,n.P(packed),ew,n.P(h1),tokens,U(1024),U(4096));
  n.Run("deep","vit_expand_blocked_fp8_tiled_bytein_m4",size_t(tokens)*4096,n.P(packed),ew,n.P(h4),tokens,U(1024),U(4096));n.Synchronize();
  std::vector<unsigned char>e1(size_t(tokens)*4096),e4(e1.size());n.api.Check(n.api.hipMemcpy(e1.data(),n.P(h1),e1.size(),2),"read expand");n.api.Check(n.api.hipMemcpy(e4.data(),n.P(h4),e4.size(),2),"read expand m4");
  size_t ediff=0,ebad=0;for(size_t i=0;i<e1.size();i++){ediff+=e1[i]!=e4[i];ebad+=(e1[i]&127)==127;}
  printf("tokens=%u pattern=%u expand_m4_bytediff=%zu invalid=%zu\n",tokens,pattern,ediff,ebad);ok=ok&&!ediff&&!ebad;
  auto fw2=n.PackedVitWeight(n.Block(31,"expand"),4096,1024,true,true);auto hf=n.New(size_t(tokens)*1024);
  n.Run("deep","vit_expand_blocked_fp8_frag_bytein",size_t(tokens)*4096,n.P(packed),fw2,n.P(hf),tokens,U(1024),U(4096));n.Synchronize();
  std::vector<unsigned char>ef(e1.size());n.api.Check(n.api.hipMemcpy(ef.data(),n.P(hf),ef.size(),2),"read expand frag");
  size_t fdiff=0;for(size_t i=0;i<e1.size();i++)fdiff+=e1[i]!=ef[i];
  printf("tokens=%u pattern=%u expand_frag_bytediff=%zu\n",tokens,pattern,fdiff);ok=ok&&!fdiff;
  auto hf4=n.New(size_t(tokens)*1024);n.Run("deep","vit_expand_blocked_fp8_frag_bytein_m4",size_t(tokens)*4096,n.P(packed),fw2,n.P(hf4),tokens,U(1024),U(4096));n.Synchronize();
  std::vector<unsigned char>ef4(e1.size());n.api.Check(n.api.hipMemcpy(ef4.data(),n.P(hf4),ef4.size(),2),"read expand frag m4");
  size_t f4diff=0;for(size_t i=0;i<e1.size();i++)f4diff+=e1[i]!=ef4[i];
  printf("tokens=%u pattern=%u expand_frag_m4_bytediff=%zu\n",tokens,pattern,f4diff);ok=ok&&!f4diff;
  auto hf2=n.New(size_t(tokens)*1024);n.Run("deep","vit_expand_blocked_fp8_frag_bytein_m2",size_t(tokens)*4096,n.P(packed),fw2,n.P(hf2),tokens,U(1024),U(4096));n.Synchronize();
  std::vector<unsigned char>ef2(e1.size());n.api.Check(n.api.hipMemcpy(ef2.data(),n.P(hf2),ef2.size(),2),"read expand frag m2");
  size_t f2diff=0;for(size_t i=0;i<e1.size();i++)f2diff+=e1[i]!=ef2[i];
  printf("tokens=%u pattern=%u expand_frag_m2_bytediff=%zu\n",tokens,pattern,f2diff);ok=ok&&!f2diff;
  auto pt=n.New(size_t(tokens)*256),hft=n.New(size_t(tokens)*1024);
  n.Run("deep","vit_pack_input_tiled",size_t(tokens)*256,n.P(cin),n.P(pt),U(tokens*1024));
  n.Run("deep","vit_expand_blocked_fp8_frag_tiledin",size_t(tokens)*4096,n.P(pt),fw2,n.P(hft),tokens,U(1024),U(4096));n.Synchronize();
  std::vector<unsigned char>eft(e1.size());n.api.Check(n.api.hipMemcpy(eft.data(),n.P(hft),eft.size(),2),"read expand tiledin");
  size_t ftdiff=0;for(size_t i=0;i<e1.size();i++)ftdiff+=e1[i]!=eft[i];
  printf("tokens=%u pattern=%u expand_tiledin_bytediff=%zu\n",tokens,pattern,ftdiff);ok=ok&&!ftdiff;
  /* byte stream: contract (byte skip in, byte out), QKV byte in, attention byte out, project byte in/out. Each stage is
     compared with the f32-stream kernel fed the equivalent f32 tensor; decoded bytes must match the f32 bits. */
  auto cw=n.PackedVitWeight(n.Block(31,"contract"),1024,4096,false);auto pw=n.PackedDeepWeight(n.Block(31,"projection"),1048576);
  auto cf=n.New(size_t(tokens)*1024),c8=n.New(size_t(tokens)*256);
  n.Run("deep","vit_contract_blocked_fp8",size_t(tokens)*1024,n.P(h1),cw,n.P(cin),n.P(cf),tokens,U(4096),U(1024));
  n.Run("deep","vit_contract_blocked_fp8_bstream",size_t(tokens)*1024,n.P(h1),cw,n.P(packed),n.P(c8),tokens,U(4096),U(1024));
  auto cff=n.New(size_t(tokens)*1024);n.Run("deep","vit_ffn_fused",size_t(tokens)*1024,n.P(packed),fw2,cw,n.P(cin),n.P(cff),tokens);n.Synchronize();
  {std::vector<float>xa(size_t(tokens)*1024),xb(xa.size());n.api.Check(n.api.hipMemcpy(xa.data(),n.P(cf),xa.size()*4,2),"read contract");n.api.Check(n.api.hipMemcpy(xb.data(),n.P(cff),xb.size()*4,2),"read fused ffn");
   size_t d=0,bad=0;for(size_t i=0;i<xa.size();i++){d+=memcmp(&xa[i],&xb[i],4)!=0;bad+=!std::isfinite(xb[i]);}printf("tokens=%u pattern=%u ffn_fused_bitdiff=%zu invalid=%zu\n",tokens,pattern,d,bad);ok=ok&&!d&&!bad;}
  auto q8a=n.New(size_t(tokens)*768),q8b=n.New(size_t(tokens)*768);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8",size_t(tokens)*3072,n.P(cf),qw,n.P(q8a),tokens);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8_bytein",size_t(tokens)*3072,n.P(c8),qw,n.P(q8b),tokens);
  auto avf=n.New(size_t(tokens)*1024),av8=n.New(size_t(tokens)*256);
  n.Run("deep",(fused+"_bytein").c_str(),size_t(tokens)*512,n.P(q8a),n.P(avf),tokens);
  n.Run("deep",(fused+"_bytein_bout").c_str(),size_t(tokens)*512,n.P(q8b),n.P(av8),tokens);
  auto pf=n.New(size_t(tokens)*1024),pb=n.New(size_t(tokens)*1024),p8=n.New(size_t(tokens)*256),pk=n.New(size_t(tokens)*256);
  n.Run("deep","vit_project",size_t(tokens)*1024,n.P(avf),pw,n.P(cf),n.P(pf),tokens,U(1024),U(1024));
  n.Run("deep","vit_project_bytein_bout",size_t(tokens)*1024,n.P(av8),pw,n.P(c8),n.P(pb),n.P(p8),tokens);
  n.Run("deep","vit_pack_input",size_t(tokens)*256,n.P(pf),n.P(pk),U(tokens*1024));n.Synchronize();
  std::vector<float>xcf(size_t(tokens)*1024),xavf(xcf.size()),xpf(xcf.size()),xpb(xcf.size());std::vector<unsigned char>xc8(xcf.size()),xav8(xcf.size()),xp8(xcf.size()),xpk(xcf.size()),xq8a(size_t(tokens)*3072),xq8b(xq8a.size());
  n.api.Check(n.api.hipMemcpy(xcf.data(),n.P(cf),xcf.size()*4,2),"read contract");n.api.Check(n.api.hipMemcpy(xc8.data(),n.P(c8),xc8.size(),2),"read contract bytes");
  n.api.Check(n.api.hipMemcpy(xq8a.data(),n.P(q8a),xq8a.size(),2),"read qkv a");n.api.Check(n.api.hipMemcpy(xq8b.data(),n.P(q8b),xq8b.size(),2),"read qkv b");
  n.api.Check(n.api.hipMemcpy(xavf.data(),n.P(avf),xavf.size()*4,2),"read av");n.api.Check(n.api.hipMemcpy(xav8.data(),n.P(av8),xav8.size(),2),"read av bytes");
  n.api.Check(n.api.hipMemcpy(xpf.data(),n.P(pf),xpf.size()*4,2),"read project");n.api.Check(n.api.hipMemcpy(xpb.data(),n.P(pb),xpb.size()*4,2),"read project b");
  n.api.Check(n.api.hipMemcpy(xp8.data(),n.P(p8),xp8.size(),2),"read project bytes");n.api.Check(n.api.hipMemcpy(xpk.data(),n.P(pk),xpk.size(),2),"read packed project");
  size_t cdiff=0,qd=0,avd=0,pd=0,p8d=0,sbad=0;
  for(size_t i=0;i<xcf.size();i++){float d=fp8(xc8[i]);cdiff+=memcmp(&d,&xcf[i],4)!=0;d=fp8(xav8[i]);avd+=memcmp(&d,&xavf[i],4)!=0;pd+=memcmp(&xpf[i],&xpb[i],4)!=0;p8d+=xp8[i]!=xpk[i];sbad+=!std::isfinite(xcf[i])||!std::isfinite(xavf[i])||!std::isfinite(xpf[i]);}
  for(size_t i=0;i<xq8a.size();i++)qd+=xq8a[i]!=xq8b[i];
  /* half stream: contract F16 out decoded must equal the f32 contract; half-input QKV (N2 and N4) must reproduce the
     byte QKV; project with half skip must reproduce the f32 project and its packed bytes. */
  auto ch=n.New(size_t(tokens)*512),q8c=n.New(size_t(tokens)*768),q8d=n.New(size_t(tokens)*768),ph=n.New(size_t(tokens)*1024),ph8=n.New(size_t(tokens)*256);
  n.Run("deep","vit_contract_blocked_fp8_hstream",size_t(tokens)*1024,n.P(h1),cw,n.P(packed),n.P(ch),tokens,U(4096),U(1024));
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8_h16in",size_t(tokens)*3072,n.P(ch),qw,n.P(q8c),tokens);
  n.Run("deep","vit_qkv_project_normalize_fused_f16compact_fp8_h16in_n4",size_t(tokens)*3072,n.P(ch),qw,n.P(q8d),tokens);
  n.Run("deep","vit_project_bytein_bout_hskip",size_t(tokens)*1024,n.P(av8),pw,n.P(ch),n.P(ph),n.P(ph8),tokens);n.Synchronize();
  std::vector<unsigned short>xch(size_t(tokens)*1024);std::vector<unsigned char>xq8c(xq8a.size()),xq8d(xq8a.size()),xph8(xcf.size());std::vector<float>xph(xcf.size());
  n.api.Check(n.api.hipMemcpy(xch.data(),n.P(ch),xch.size()*2,2),"read half contract");n.api.Check(n.api.hipMemcpy(xq8c.data(),n.P(q8c),xq8c.size(),2),"read qkv c");n.api.Check(n.api.hipMemcpy(xq8d.data(),n.P(q8d),xq8d.size(),2),"read qkv d");
  n.api.Check(n.api.hipMemcpy(xph.data(),n.P(ph),xph.size()*4,2),"read project h");n.api.Check(n.api.hipMemcpy(xph8.data(),n.P(ph8),xph8.size(),2),"read project h bytes");
  size_t hcd=0,hq2=0,hq4=0,hpd=0,hp8=0;
  for(size_t i=0;i<xcf.size();i++){unsigned h=xch[i];unsigned sgn=(h&0x8000u)<<16,ex=(h>>10)&31u,mn=h&1023u;float d;if(!ex)d=std::ldexp(float(mn),-24)*(sgn?-1.f:1.f);else{unsigned u=sgn|((ex+112u)<<23)|(mn<<13);memcpy(&d,&u,4);}if(!ex&&!mn){unsigned u=sgn;memcpy(&d,&u,4);}hcd+=memcmp(&d,&xcf[i],4)!=0;hpd+=memcmp(&xph[i],&xpf[i],4)!=0;hp8+=xph8[i]!=xpk[i];}
  for(size_t i=0;i<xq8a.size();i++){hq2+=xq8c[i]!=xq8a[i];hq4+=xq8d[i]!=xq8a[i];}
  printf("tokens=%u pattern=%u halfstream contract_diff=%zu qkv_h16_diff=%zu qkv_n4_diff=%zu project_diff=%zu project_bytediff=%zu\n",tokens,pattern,hcd,hq2,hq4,hpd,hp8);ok=ok&&!hcd&&!hq2&&!hq4&&!hpd&&!hp8;
  printf("tokens=%u pattern=%u stream contract_diff=%zu qkv_diff=%zu attn_diff=%zu project_diff=%zu project_bytediff=%zu invalid=%zu\n",tokens,pattern,cdiff,qd,avd,pd,p8d,sbad);ok=ok&&!cdiff&&!qd&&!avd&&!pd&&!p8d&&!sbad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_vit_attn_fused ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_deep=o.fast_vit=o.packed_weights=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);
 printf(ok?"fused attention matches\n":"fused attention MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

// Bit-exactness of the MH byte residual stream against the f32 stream, per C64/128/256, mapped/identity, two patterns:
// (1) fused FFN/QKV with byte feature output (_fb) decodes to the f32 feature bit for bit, QKV bytes identical;
// (2) the same with byte block input (_bytein_fb) equals the f32-input result; (3) attention-project reading the byte
// feature (_fb) equals the f32 kernel, and its byte output (_fb_bout) decodes to the f32 output bit for bit, for post 4
// (F) and post 0 (F(Hrtz)), with and without crop. Inputs are E4M3-lattice values (what the chain carries).
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cstdio>
#include <cmath>
#include <cstring>
static float fp8(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference {
struct LayerBenchmark {
 static bool Check(Network&n,U c,U block,bool mapped,U pattern,bool diag=false){
  U w=mapped?13:16,h=16,sx=mapped?4:0,sy=sx,ww=mapped?24:16,hh=mapped?24:16,tokens=ww*hh;bool ok=true;
  std::vector<unsigned char>x8(size_t(w)*h*c);std::vector<float>x(x8.size());
  for(size_t i=0;i<x8.size();i++){unsigned code=pattern?unsigned((i*37+i/31+5)%127):unsigned((i*53+i/17+11)%127);if(i%3==0)code|=128;x8[i]=static_cast<unsigned char>(code);x[i]=fp8(code);}
  auto in=n.Upload(x.data(),x.size()*4),in8=n.Upload(x8.data(),x8.size());
  auto fw=n.PackedFusedMhWeight(n.Block(block,"ffn"),c),aw=diag?n.PackedMhWeightDiag(n.Block(block,"attention"),c):n.PackedMhWeight(n.Block(block,"attention"),c,true);
  std::string stem="mh_ffn_fused_c"+std::to_string(c)+(c==256?"_tiled":"")+"_project"+(mapped?"_mapped":"")+"_g128_qkv";
  auto fr=n.New(size_t(tokens)*c),nr=n.New(size_t(tokens)*3*c/4),f8=n.New(size_t(tokens)*c/4),n8=n.New(size_t(tokens)*3*c/4),f8b=n.New(size_t(tokens)*c/4),n8b=n.New(size_t(tokens)*3*c/4);
  n.Run("mh_fast",stem.c_str(),size_t(tokens)*c,n.P(in),fw,aw,n.P(fr),n.P(nr),tokens,w,h,ww,sx,sy);
  n.Run("mh_fast",(stem+"_fb").c_str(),size_t(tokens)*c,n.P(in),fw,aw,n.P(f8),n.P(n8),tokens,w,h,ww,sx,sy);
  n.Run("mh_fast",(stem+"_bytein_fb").c_str(),size_t(tokens)*c,n.P(in8),fw,aw,n.P(f8b),n.P(n8b),tokens,w,h,ww,sx,sy);n.Synchronize();
  std::vector<float>a(size_t(tokens)*c);std::vector<unsigned char>b(a.size()),bb(a.size()),qa(size_t(tokens)*3*c),qb(qa.size()),qc(qa.size());
  n.api.Check(n.api.hipMemcpy(a.data(),n.P(fr),a.size()*4,2),"f32 feature");n.api.Check(n.api.hipMemcpy(b.data(),n.P(f8),b.size(),2),"byte feature");n.api.Check(n.api.hipMemcpy(bb.data(),n.P(f8b),bb.size(),2),"bytein feature");
  n.api.Check(n.api.hipMemcpy(qa.data(),n.P(nr),qa.size(),2),"f32 qkv");n.api.Check(n.api.hipMemcpy(qb.data(),n.P(n8),qb.size(),2),"fb qkv");n.api.Check(n.api.hipMemcpy(qc.data(),n.P(n8b),qc.size(),2),"bytein qkv");
  size_t fd=0,fbd=0,qd=0,qbd=0,bad=0;for(size_t i=0;i<a.size();i++){float d=fp8(b[i]);fd+=memcmp(&d,&a[i],4)!=0;fbd+=b[i]!=bb[i];bad+=!std::isfinite(a[i]);}for(size_t i=0;i<qa.size();i++){qd+=qa[i]!=qb[i];qbd+=qb[i]!=qc[i];bad+=((qa[i]&127)==127);}
  printf("C=%u mapped=%u pattern=%u feature_bytediff=%zu bytein_diff=%zu qkv_diff=%zu qkv_bytein_diff=%zu invalid=%zu\n",c,mapped,pattern,fd,fbd,qd,qbd,bad);ok=ok&&!fd&&!fbd&&!qd&&!qbd&&!bad;
  std::string proj="c"+std::to_string(c)+"_attention_project";U windows=tokens/64;
  for(U post:{4u,0u})for(U crop=0;crop<(mapped?2u:1u);crop++){U cropw=crop?w:0,croph=crop?h:0,count=crop?w*h*c:tokens*c;
   auto of=n.New(size_t(count)),ofb=n.New(size_t(count)),ob=n.New(size_t(count)/4);
   n.Run("mh_fused",(proj+(diag?"_diag":"")).c_str(),windows,n.P(nr),aw,n.P(fr),n.P(of),ww,hh,post,cropw,croph,sx,sy);
   n.Run("mh_fused",(proj+(diag?"_fb_diag":"_fb")).c_str(),windows,n.P(n8),aw,n.P(f8),n.P(ofb),ww,hh,post,cropw,croph,sx,sy);
   n.Run("mh_fused",(proj+(diag?"_fb_bout_diag":"_fb_bout")).c_str(),windows,n.P(n8),aw,n.P(f8),n.P(ob),ww,hh,post,cropw,croph,sx,sy);n.Synchronize();
   std::vector<float>r(count),rb(count);std::vector<unsigned char>r8(count);
   n.api.Check(n.api.hipMemcpy(r.data(),n.P(of),count*4,2),"f32 out");n.api.Check(n.api.hipMemcpy(rb.data(),n.P(ofb),count*4,2),"fb out");n.api.Check(n.api.hipMemcpy(r8.data(),n.P(ob),count,2),"byte out");
   size_t d1=0,d2=0,inv=0;for(size_t i=0;i<count;i++){d1+=memcmp(&r[i],&rb[i],4)!=0;float d=fp8(r8[i]);d2+=memcmp(&d,&r[i],4)!=0;inv+=!std::isfinite(r[i]);}
   printf("C=%u mapped=%u pattern=%u post=%u crop=%u project_fb_bitdiff=%zu byteout_bitdiff=%zu invalid=%zu\n",c,mapped,pattern,post,crop,d1,d2,inv);ok=ok&&!d1&&!d2&&!inv;
  }
  return ok;
 }
};
}
int main(int argc,char**argv){try{if(argc!=3&&argc!=4)throw std::runtime_error("test_mh_byte_stream ASSETS MODULES [diag]");const bool diag=argc==4;if(diag&&strcmp(argv[3],"diag"))throw std::runtime_error("unknown mode");printf("diag=%u\n",diag);hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.pooled=o.fast_mh=o.mh_wave=o.packed_weights=o.tiled_mh_ffn=o.grouped_mh_contract=true;o.fused_mh_ffn=o.fp8_middle=o.fp8_ffn=o.fused_ffn_project=o.fused_qkv_norm=o.fp8_normalized=o.fused_mh=o.fp8_av=true;o.tiled_ffn_min_c=256;hip_reference::Network n(o);bool ok=true;for(unsigned c:{64u,128u,256u})for(bool mapped:{false,true})for(unsigned pattern:{0u,1u})ok=hip_reference::LayerBenchmark::Check(n,c,c==64?5:c==128?9:15,mapped,pattern,diag)&&ok;printf(ok?"byte stream matches\n":"byte stream MISMATCH\n");return ok?0:1;}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

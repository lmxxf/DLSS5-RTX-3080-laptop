// split_projection_blocked_t8 (f32 + E4M3 tiles) against split_projection_blocked, and mh_qkv_normalize_frag_c512 (tiles +
// fragment weights) against mh_qkv_normalize_fused (f32 input): real block23/40 weights, synthetic lattice input.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 for(U block:{23u,40u})for(U tokens:{1600u,960u,2160u})for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>v(size_t(tokens)*512),sk(v.size());for(size_t i=0;i<v.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%120):unsigned((i*37+i/17+5)%96);if(i%3==0)code|=128;v[i]=fp8v(code);unsigned c2=(i*41+i/23+7)%110;if(i%5==0)c2|=128;sk[i]=fp8v(c2);}
  auto in=n.Upload(v.data(),v.size()*4),skip=n.Upload(sk.data(),sk.size()*4);auto pw=n.PackedDeepWeight(n.Block(block,"ffwd-projection"),262144);
  auto pa=n.New(size_t(tokens)*512),pb=n.New(size_t(tokens)*512),t8=n.New(size_t(tokens)*128);
  n.Run("deep","split_projection_blocked",size_t(tokens)*512,n.P(in),pw,n.P(skip),n.P(pa),tokens);
  n.Run("deep","split_projection_blocked_t8",size_t(tokens)*512,n.P(in),pw,n.P(skip),n.P(pb),n.P(t8),tokens);
  /* tiled contract + fragment projection: contract f32 and tiles, then projection f32/tiles against split_projection_blocked_t8 */
  {auto fw2=n.PackedSplitFfnWeight(n.Block(block,"ffwd"));auto ca=n.New(size_t(tokens)*512),cb=n.New(size_t(tokens)*512),c8=n.New(size_t(tokens)*128),pf=n.New(size_t(tokens)*512),pf8=n.New(size_t(tokens)*128);
   n.Run("deep","split_ffn_fused_fp8",size_t(tokens)*512,n.P(in),fw2,n.P(ca),tokens);
   n.Run("deep","split_ffn_fused_fp8_t8",size_t(tokens)*512,n.P(in),fw2,n.P(cb),n.P(c8),tokens);
   n.Run("deep","split_projection_frag",size_t(tokens)*512,n.P(c8),n.PackedSplitProjectionFrag(n.Block(block,"ffwd-projection")),n.P(skip),n.P(pf),n.P(pf8),tokens);
   auto pr=n.New(size_t(tokens)*512),pr8=n.New(size_t(tokens)*128);n.Run("deep","split_projection_blocked_t8",size_t(tokens)*512,n.P(ca),pw,n.P(skip),n.P(pr),n.P(pr8),tokens);n.Synchronize();
   std::vector<float>fa(size_t(tokens)*512),fb(fa.size()),qa2(fa.size()),qb2(fa.size());std::vector<unsigned char>t1(fa.size()),t2(fa.size()),t3(fa.size());
   n.api.Check(n.api.hipMemcpy(fa.data(),n.P(ca),fa.size()*4,2),"c");n.api.Check(n.api.hipMemcpy(fb.data(),n.P(cb),fb.size()*4,2),"c t8");n.api.Check(n.api.hipMemcpy(t1.data(),n.P(c8),t1.size(),2),"c tiles");
   n.api.Check(n.api.hipMemcpy(qa2.data(),n.P(pr),qa2.size()*4,2),"p");n.api.Check(n.api.hipMemcpy(qb2.data(),n.P(pf),qb2.size()*4,2),"p frag");n.api.Check(n.api.hipMemcpy(t2.data(),n.P(pr8),t2.size(),2),"p tiles");n.api.Check(n.api.hipMemcpy(t3.data(),n.P(pf8),t3.size(),2),"p frag tiles");
   size_t cd=0,ct=0,pd2=0,pt=0;for(size_t i=0;i<fa.size();i++){cd+=memcmp(&fa[i],&fb[i],4)!=0;size_t r=i/512,c=i%512;size_t ti=((r/16)*16+c/32)*512+(r%16)*32+c%32;ct+=t1[ti]!=ExactWeightFp8(fa[i]);pd2+=memcmp(&qa2[i],&qb2[i],4)!=0;pt+=t2[ti]!=t3[ti];}
   printf("block=%u tokens=%u pattern=%u contract_bitdiff=%zu contract_tilediff=%zu projfrag_bitdiff=%zu projfrag_tilediff=%zu\n",block,tokens,pattern,cd,ct,pd2,pt);ok=ok&&!cd&&!ct&&!pd2&&!pt;}
  auto aw=n.PackedMhWeight(n.Block(block,"attention"),512,true),fw=n.PackedMhWeightQkvFrag(n.Block(block,"attention"),512);auto qa=n.New(size_t(tokens)*384),qb=n.New(size_t(tokens)*384);
  n.Run("mh_fast","mh_qkv_normalize_fused",size_t(tokens)*1536,n.P(pa),aw,n.P(qa),tokens,U(512));
  n.Run("mh_fast","mh_qkv_normalize_frag_c512",size_t(tokens)*1536,n.P(t8),fw,n.P(qb),tokens);n.Synchronize();
  std::vector<float>xa(size_t(tokens)*512),xb(xa.size());std::vector<unsigned char>x8(xa.size()),ya(size_t(tokens)*1536),yb(ya.size());
  n.api.Check(n.api.hipMemcpy(xa.data(),n.P(pa),xa.size()*4,2),"proj");n.api.Check(n.api.hipMemcpy(xb.data(),n.P(pb),xb.size()*4,2),"proj t8");n.api.Check(n.api.hipMemcpy(x8.data(),n.P(t8),x8.size(),2),"tiles");
  n.api.Check(n.api.hipMemcpy(ya.data(),n.P(qa),ya.size(),2),"qkv");n.api.Check(n.api.hipMemcpy(yb.data(),n.P(qb),yb.size(),2),"qkv frag");
  size_t pd=0,td=0,qd=0,bad=0;for(size_t i=0;i<xa.size();i++){pd+=memcmp(&xa[i],&xb[i],4)!=0;size_t r=i/512,c=i%512;unsigned char exp=ExactWeightFp8(xa[i]);td+=x8[((r/16)*16+c/32)*512+(r%16)*32+c%32]!=exp;bad+=!std::isfinite(xa[i]);}
  for(size_t i=0;i<ya.size();i++)qd+=ya[i]!=yb[i];
  /* attention projection: synthetic AV bytes, feature = projection output, crop (50x32 work grid, 46x28 valid at 2,2) and no crop, post 0 and 3 */
  for(unsigned mode=0;mode<3;mode++){U workw=tokens==1600?50:tokens==960?40:60,workh=tokens/workw,cropw=mode==0?workw:workw-4,croph=mode==0?workh:workh-4,csx=mode==0?0:2,csy=csx,post=mode==2?3:0;
   std::vector<unsigned char>avv(size_t(tokens)*512);for(size_t i=0;i<avv.size();i++){unsigned code=(i*31+i/19+pattern*7)%118;if(i%4==0)code|=128;avv[i]=(unsigned char)code;}
   auto av=n.Upload(avv.data(),avv.size());size_t outn=(cropw?size_t(cropw)*croph:size_t(tokens))*512;auto oa=n.New(outn),ob=n.New(outn);
   n.Run("mh_fast","mh_attention_crop",size_t(tokens)*512,n.P(av),n.P(pa),aw,n.P(oa),tokens,post,cropw,croph,workw,csx,csy,U(512));
   n.Run("mh_fast","mh_attention_project_frag_c512",size_t(tokens)*512,n.P(av),n.P(pa),fw,n.P(ob),tokens,post,cropw,croph,workw,csx,csy);n.Synchronize();
   std::vector<float>za(outn),zb(outn);n.api.Check(n.api.hipMemcpy(za.data(),n.P(oa),outn*4,2),"proj ref");n.api.Check(n.api.hipMemcpy(zb.data(),n.P(ob),outn*4,2),"proj frag");
   size_t d=0,b2=0;for(size_t i=0;i<outn;i++){d+=memcmp(&za[i],&zb[i],4)!=0;b2+=!std::isfinite(za[i]);}
   printf("block=%u tokens=%u pattern=%u attnproj mode=%u bitdiff=%zu invalid=%zu\n",block,tokens,pattern,mode,d,b2);ok=ok&&!d&&!b2;}
  printf("block=%u tokens=%u pattern=%u proj_bitdiff=%zu tile_bytediff=%zu qkv_bytediff=%zu invalid=%zu\n",block,tokens,pattern,pd,td,qd,bad);ok=ok&&!pd&&!td&&!qd&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_c512_qkv_frag ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_deep=o.fp8_deep=o.fast_mh=o.mh_wave=o.packed_weights=o.pooled=o.fused_mh=o.fp8_normalized=o.fused_qkv_norm=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"c512 qkv frag matches\n":"c512 qkv frag MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

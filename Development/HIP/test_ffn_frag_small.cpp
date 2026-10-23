// C64/C128 fragment-weight FFN+project+QKV twins (mh_ffn_fused_c{64,128}_tiled_project[_mapped]_g128_qkv, PackedFusedMhWeight force_tiled)
// against the separate FFN + mh_qkv_normalize_fused reference and against the untiled fused kernel: real block weights, two input patterns, mapped and plain.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cstdio>
#include <cmath>
namespace hip_reference {
struct LayerBenchmark {
 static bool Check(Network&n,U c,U block,bool mapped,U pattern){
  U w=mapped?13:16,h=16,sx=mapped?4:0,sy=sx,ww=mapped?24:16,hh=mapped?24:16,tokens=ww*hh;
  std::vector<float>v(size_t(w)*h*c);for(size_t i=0;i<v.size();i++){unsigned code=(i*37+i/31)%127;float x=(code>>3)?std::ldexp(1.f+float(code&7)/8,int(code>>3)-7):float(code&7)/512;v[i]=pattern?float(int((i*73)%2048)-1024)/512.f:(i&1?-x:x);}
  auto in=n.Upload(v.data(),v.size()*4),fr=n.New(size_t(tokens)*c),fg=n.New(size_t(tokens)*c),nr=n.New(size_t(tokens)*3*c/4),ng=n.New(size_t(tokens)*3*c/4);
  auto fw=n.PackedFusedMhWeight(n.Block(block,"ffn"),c),aw=n.PackedMhWeight(n.Block(block,"attention"),c,true);
  std::string stem="mh_ffn_fused_c"+std::to_string(c)+"_project"+(mapped?"_mapped":"")+"_g128",tstem="mh_ffn_fused_c"+std::to_string(c)+"_frag_project"+(mapped?"_mapped":"")+"_g128";auto ft=n.PackedFusedMhWeightFrag(n.Block(block,"ffn"),c),at=n.PackedMhWeightQkvFragOnly(n.Block(block,"attention"),c);
  if(mapped)n.Run("mh_fast",stem.c_str(),size_t(tokens)*c,n.P(in),fw,n.P(fr),tokens,w,h,ww,sx,sy);else n.Run("mh_fast",stem.c_str(),size_t(tokens)*c,n.P(in),fw,n.P(fr),tokens);
  n.Run("mh_fast","mh_qkv_normalize_fused",size_t(tokens)*3*c,n.P(fr),aw,n.P(nr),tokens,c);
  n.Run("mh_fast",(tstem+"_qkv").c_str(),size_t(tokens)*c,n.P(in),ft,at,n.P(fg),n.P(ng),tokens,w,h,ww,sx,sy);
  auto fb=n.New(size_t(tokens)*c),nb=n.New(size_t(tokens)*3*c/4);n.Run("mh_fast",(stem+"_qkv").c_str(),size_t(tokens)*c,n.P(in),fw,aw,n.P(fb),n.P(nb),tokens,w,h,ww,sx,sy);n.Synchronize();
  std::vector<float>a(size_t(tokens)*c),b(a.size());std::vector<unsigned char>x(size_t(tokens)*3*c),y(x.size());
  n.api.Check(n.api.hipMemcpy(a.data(),n.P(fr),a.size()*4,2),"FFN reference");n.api.Check(n.api.hipMemcpy(b.data(),n.P(fg),b.size()*4,2),"FFN fused");n.api.Check(n.api.hipMemcpy(x.data(),n.P(nr),x.size(),2),"QKV reference");n.api.Check(n.api.hipMemcpy(y.data(),n.P(ng),y.size(),2),"QKV fused");
  size_t fd=0,qd=0,bad=0;for(size_t i=0;i<a.size();i++){fd+=memcmp(&a[i],&b[i],4)!=0;bad+=!std::isfinite(a[i])||!std::isfinite(b[i]);}for(size_t i=0;i<x.size();i++){qd+=x[i]!=y[i];bad+=((x[i]&127)==127)||((y[i]&127)==127);}
  size_t bfd=0,bqd=0;{std::vector<float>bb(a.size());std::vector<unsigned char>yb(x.size());n.api.Check(n.api.hipMemcpy(bb.data(),n.P(fb),bb.size()*4,2),"FFN bn");n.api.Check(n.api.hipMemcpy(yb.data(),n.P(nb),yb.size(),2),"QKV bn");for(size_t i=0;i<a.size();i++)bfd+=memcmp(&a[i],&bb[i],4)!=0;for(size_t i=0;i<x.size();i++)bqd+=x[i]!=yb[i];}
  printf("C=%u mapped=%u pattern=%u ffn_bitdiff=%zu qkv_bytediff=%zu invalid=%zu unfrag_ffn_bitdiff=%zu unfrag_qkv_bytediff=%zu\n",c,mapped,pattern,fd,qd,bad,bfd,bqd);return !fd&&!qd&&!bad&&!bfd&&!bqd;
 }
};
}
int main(int argc,char**argv){try{if(argc!=3)throw std::runtime_error("test_ffn_frag_small ASSETS MODULES");hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.pooled=o.fast_mh=o.mh_wave=o.packed_weights=o.tiled_mh_ffn=o.grouped_mh_contract=true;o.fused_mh_ffn=o.fp8_middle=o.fp8_ffn=o.fused_ffn_project=o.fused_qkv_norm=o.fp8_normalized=o.fused_mh=true;o.tiled_ffn_min_c=256;hip_reference::Network n(o);bool ok=true;for(unsigned c:{64u,128u})for(bool mapped:{false,true})for(unsigned pattern:{0u,1u})ok=hip_reference::LayerBenchmark::Check(n,c,c==64?5:c==128?9:15,mapped,pattern)&&ok;return ok?0:1;}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

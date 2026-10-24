// c64_attention_project_w16 against c64_attention_project: real block5 attention weights, synthetic E4M3 normalized
// Q/K/V bytes and lattice feature floats, 400x256 (900p) and 320x192 windows, post 4 and 0, crop and no crop.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 struct G{U w,h,post,cropw,croph,sx,sy;};G gs[]={{400,256,4,0,0,0,0},{400,256,0,0,0,0,0},{408,264,4,400,256,4,4},{320,192,3,0,0,0,0}};
 auto aw=n.PackedMhWeight(n.Block(5,"attention"),64,true);
 for(auto&g:gs)for(unsigned pattern=0;pattern<2;pattern++){
  size_t tokens=size_t(g.w)*g.h;std::vector<unsigned char>q(tokens*3*64);for(size_t i=0;i<q.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%100):unsigned((i*37+i/17+5)%88);if(i%3==0)code|=128;q[i]=(unsigned char)code;}
  std::vector<float>f(tokens*64);for(size_t i=0;i<f.size();i++){unsigned code=pattern?unsigned((i*41+i/23+7)%110):unsigned((i*29+i/13+3)%90);if(i%5==0)code|=128;f[i]=fp8v(code);}
  auto norm=n.Upload(q.data(),q.size()),feat=n.Upload(f.data(),f.size()*4);size_t outn=(g.cropw?size_t(g.cropw)*g.croph:tokens)*64;auto a=n.New(outn),b=n.New(outn);
  U windows=(g.w/8)*(g.h/8);
  n.Run("mh_fused","c64_attention_project",windows,n.P(norm),aw,n.P(feat),n.P(a),g.w,g.h,g.post,g.cropw,g.croph,g.sx,g.sy);
  n.Run("mh_fused","c64_attention_project_w16",windows,n.P(norm),aw,n.P(feat),n.P(b),g.w,g.h,g.post,g.cropw,g.croph,g.sx,g.sy);n.Synchronize();
  std::vector<float>x(outn),y(outn);n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),outn*4,2),"ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),outn*4,2),"w16");
  size_t diff=0,bad=0;for(size_t i=0;i<outn;i++){diff+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}
  printf("%ux%u post=%u crop=%ux%u pattern=%u bitdiff=%zu invalid=%zu\n",g.w,g.h,g.post,g.cropw,g.croph,pattern,diff,bad);ok=ok&&!diff&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_c64_attn_w16 ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_mh=o.mh_wave=o.packed_weights=o.pooled=o.fused_mh=o.fp8_normalized=o.fp8_av=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"c64 attention w16 matches\n":"c64 attention w16 MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

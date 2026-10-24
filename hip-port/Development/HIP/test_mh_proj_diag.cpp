// c{64,128,256}_attention_project_diag (residual as prepacked diagonal fragment MMAs) against the scalar-residual production
// kernels: real attention weights per channel width, synthetic E4M3 normalized Q/K/V bytes and lattice feature floats,
// 400x256 (900p) and 320x192 windows, post 4/0/3, crop and no crop.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 struct G{U w,h,post,cropw,croph,sx,sy;};G gs[]={{400,256,4,0,0,0,0},{400,256,0,0,0,0,0},{408,264,4,400,256,4,4},{320,192,3,0,0,0,0}};
 struct B{U c,block;};B bs[]={{64,5},{64,63},{128,9},{128,58},{256,15},{256,50}};
 for(auto&bb:bs){U c=bb.c;auto aw=n.PackedMhWeight(n.Block(bb.block,"attention"),c,true),dw=n.PackedMhWeightDiag(n.Block(bb.block,"attention"),c);std::string base="c"+std::to_string(c)+"_attention_project";
 for(auto&g:gs)for(unsigned pattern=0;pattern<2;pattern++){
  size_t tokens=size_t(g.w)*g.h;std::vector<unsigned char>q(tokens*3*c);for(size_t i=0;i<q.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%100):unsigned((i*37+i/17+5)%88);if(i%3==0)code|=128;q[i]=(unsigned char)code;}
  std::vector<float>f(tokens*c);for(size_t i=0;i<f.size();i++){unsigned code=pattern?unsigned((i*41+i/23+7)%110):unsigned((i*29+i/13+3)%90);if(i%5==0)code|=128;f[i]=fp8v(code);}
  auto norm=n.Upload(q.data(),q.size()),feat=n.Upload(f.data(),f.size()*4);size_t outn=(g.cropw?size_t(g.cropw)*g.croph:tokens)*c;auto a=n.New(outn),b=n.New(outn);
  U windows=(g.w/8)*(g.h/8);
  n.Run("mh_fused",base.c_str(),windows,n.P(norm),aw,n.P(feat),n.P(a),g.w,g.h,g.post,g.cropw,g.croph,g.sx,g.sy);
  n.Run("mh_fused",(base+"_diag").c_str(),windows,n.P(norm),dw,n.P(feat),n.P(b),g.w,g.h,g.post,g.cropw,g.croph,g.sx,g.sy);n.Synchronize();
  std::vector<float>x(outn),y(outn);n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),outn*4,2),"ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),outn*4,2),"diag");
  size_t diff=0,bad=0;for(size_t i=0;i<outn;i++){diff+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}
  printf("c=%u block=%u %ux%u post=%u crop=%ux%u pattern=%u bitdiff=%zu invalid=%zu\n",c,bb.block,g.w,g.h,g.post,g.cropw,g.croph,pattern,diff,bad);ok=ok&&!diff&&!bad;
 }}
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_mh_proj_diag ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_mh=o.mh_wave=o.packed_weights=o.pooled=o.fused_mh=o.fp8_normalized=o.fp8_av=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"mh projection diag matches\n":"mh projection diag MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

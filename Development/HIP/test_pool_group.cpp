// mh_pool_project_group_c{64,128,256} (group-shared pooling, fragment weights) against mh_pool + mh_pool_project_production: synthetic raw (arbitrary floats and
// lattice values), production geometries (400x256->200x128 c64, 200x128->100x64 c128, 100x64->50x32 c256) plus the
// 1080p head rectangle (60x36->32x20 valid 30x18, c256). Output floats must match bit for bit.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 struct G{U w,h,c,ow,oh,vw,vh;const char*file;};G gs[]={{800,512,32,400,256,0,0,"block4-ds.f32"},{400,256,64,200,128,0,0,"block8-ds.f32"},{200,128,128,100,64,0,0,"block14-ds.f32"},{100,64,256,50,32,0,0,"block22-ds.f32"},{60,36,256,32,20,30,18,"head-matrix.f32"}};
 for(auto&g:gs)for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>v(size_t(g.w)*g.h*g.c);for(size_t i=0;i<v.size();i++){unsigned code=(i*37+i/29+pattern*5)%251;v[i]=pattern?float(int(code)-125)/37.f:std::ldexp(float((code&7)+8),int(code>>3)%20-12)*((i&1)?-1.f:1.f);}
  auto raw=n.Upload(v.data(),v.size()*4);size_t M=size_t(g.ow)*g.oh,N=2*g.c;auto pooled=n.New(M*g.c),ref=n.New(M*N),fused=n.New(M*N);
  n.Run("mh","mh_pool",M*g.c,n.P(raw),n.P(pooled),g.ow,g.oh,g.w,g.vw,g.vh,g.c);
  n.Run("mh_fast","mh_pool_project_production",M*N,n.P(pooled),n.Weight(g.file),n.P(ref),g.ow,g.oh,g.vw,g.vh,g.c);
  if(g.c!=32)n.Run("mh_fast",("mh_pool_project_group_c"+std::to_string(g.c)).c_str(),M*N,n.P(raw),n.PackedDsWeightFrag(g.file,g.c),n.P(fused),g.ow,g.oh,g.w,g.vw,g.vh);else n.Run("mh_fast","mh_pool_project_production",M*N,n.P(pooled),n.Weight(g.file),n.P(fused),g.ow,g.oh,g.vw,g.vh,g.c);
  auto hw=n.New(M*N);n.Run("mh_fast","mh_pool_project_production_h16w",M*N,n.P(pooled),n.PackedDsWeightCast(g.file,g.c),n.P(hw),g.ow,g.oh,g.vw,g.vh,g.c);n.Synchronize();
  std::vector<float>a(M*N),b(M*N);n.api.Check(n.api.hipMemcpy(a.data(),n.P(ref),a.size()*4,2),"ref");n.api.Check(n.api.hipMemcpy(b.data(),n.P(fused),b.size()*4,2),"fused");
  std::vector<float>hb(M*N);n.api.Check(n.api.hipMemcpy(hb.data(),n.P(hw),hb.size()*4,2),"h16w");
  size_t diff=0,bad=0,hd=0;float maxabs=0;for(size_t i=0;i<a.size();i++){diff+=memcmp(&a[i],&b[i],4)!=0;hd+=memcmp(&a[i],&hb[i],4)!=0;bad+=!std::isfinite(a[i])||!std::isfinite(b[i]);maxabs=std::fmax(maxabs,std::fabs(a[i]-b[i]));}
  printf("c=%u %ux%u->%ux%u valid=%ux%u pattern=%u bitdiff=%zu h16w_bitdiff=%zu invalid=%zu maxabs=%g\n",g.c,g.w,g.h,g.ow,g.oh,g.vw,g.vh,pattern,diff,hd,bad,maxabs);ok=ok&&!diff&&!hd&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_pool_group ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_mh=o.mh_wave=o.packed_weights=o.pooled=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"pool project matches\n":"pool project MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

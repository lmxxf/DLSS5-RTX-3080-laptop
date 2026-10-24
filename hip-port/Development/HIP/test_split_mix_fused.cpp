// split_ffn_fused_fp8_mix against split_mix_blocked + split_ffn_fused_fp8: real block23/block40 ffwd weights, synthetic
// lattice input (1600/960/2160 tokens), contract output floats must match bit for bit.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 for(U block:{23u,40u})for(U tokens:{1600u,960u,2160u})for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>v(size_t(tokens)*512);for(size_t i=0;i<v.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%120):unsigned((i*37+i/17+5)%96);if(i%3==0)code|=128;v[i]=fp8v(code);}
  auto in=n.Upload(v.data(),v.size()*4);auto fw=n.Weight(n.Block(block,"ffwd")),pw=n.PackedSplitFfnWeight(n.Block(block,"ffwd"));
  auto mixed=n.New(size_t(tokens)*512),a=n.New(size_t(tokens)*512),b=n.New(size_t(tokens)*512);
  n.Run("deep","split_mix_blocked",size_t(tokens)*512,n.P(in),fw,n.P(mixed),tokens);
  n.Run("deep","split_ffn_fused_fp8",size_t(tokens)*512,n.P(mixed),pw,n.P(a),tokens);
  n.Run("deep","split_ffn_fused_fp8_mix",size_t(tokens)*512,n.P(in),pw,n.P(b),tokens);n.Synchronize();
  std::vector<float>x(size_t(tokens)*512),y(x.size());n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),x.size()*4,2),"ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),y.size()*4,2),"fused");
  size_t diff=0,bad=0;for(size_t i=0;i<x.size();i++){diff+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}
  auto hw=n.PackedSplitFfnWeightMixHalf(n.Block(block,"ffwd"));auto m2=n.New(size_t(tokens)*512);n.Run("deep","split_mix_blocked_h16w",size_t(tokens)*512,n.P(in),hw,n.P(m2),tokens);n.Synchronize();
  std::vector<float>xm(size_t(tokens)*512),ym(xm.size());n.api.Check(n.api.hipMemcpy(xm.data(),n.P(mixed),xm.size()*4,2),"mix");n.api.Check(n.api.hipMemcpy(ym.data(),n.P(m2),ym.size()*4,2),"mix h16w");
  size_t md=0;for(size_t i=0;i<xm.size();i++)md+=memcmp(&xm[i],&ym[i],4)!=0;
  printf("block=%u tokens=%u pattern=%u bitdiff=%zu invalid=%zu mix_h16w_bitdiff=%zu\n",block,tokens,pattern,diff,bad,md);ok=ok&&!diff&&!bad&&!md;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_split_mix_fused ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_deep=o.fp8_deep=o.packed_weights=o.pooled=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"split mix fused matches\n":"split mix fused MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

// mh_qkv_normalize_wave_c512 against mh_qkv_normalize_fused (fast_dense<Normalize>): real block23/40 attention weights,
// synthetic lattice-valued input, 1600/960/2160 tokens (900p/720p/1080p C512 geometry). Output bytes must be identical.
#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
#include <cstring>
static float fp8v(unsigned b){unsigned e=(b>>3)&15,m=b&7;float x=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-x:x;}
namespace hip_reference { struct LayerBenchmark { static bool Check(Network&n){bool ok=true;
 for(U block:{23u,40u})for(U tokens:{1600u,960u,2160u})for(unsigned pattern=0;pattern<2;pattern++){
  std::vector<float>v(size_t(tokens)*512);for(size_t i=0;i<v.size();i++){unsigned code=pattern?unsigned((i*53+i/31+11)%120):unsigned((i*37+i/17+5)%96);if(i%3==0)code|=128;v[i]=fp8v(code);}
  auto in=n.Upload(v.data(),v.size()*4);auto w=n.PackedMhWeight(n.Block(block,"attention"),512,true);auto a=n.New(size_t(tokens)*384),b=n.New(size_t(tokens)*384);
  n.Run("mh_fast","mh_qkv_normalize_fused",size_t(tokens)*1536,n.P(in),w,n.P(a),tokens,U(512));
  n.Run("mh_fast","mh_qkv_normalize_wave_c512",size_t(tokens)*1536,n.P(in),w,n.P(b),tokens);n.Synchronize();
  std::vector<unsigned char>x(size_t(tokens)*1536),y(x.size());n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),x.size(),2),"ref");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),y.size(),2),"wave");
  size_t diff=0,bad=0;for(size_t i=0;i<x.size();i++){diff+=x[i]!=y[i];bad+=((x[i]&127)==127)||((y[i]&127)==127);}
  printf("block=%u tokens=%u pattern=%u bytediff=%zu invalid=%zu\n",block,tokens,pattern,diff,bad);ok=ok&&!diff&&!bad;
 }
 return ok;}}; }
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("test_c512_qkv_wave ASSETS MODULES");
 hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_mh=o.mh_wave=o.packed_weights=o.pooled=o.fused_mh=o.fp8_normalized=o.fused_qkv_norm=true;
 hip_reference::Network n(o);bool ok=hip_reference::LayerBenchmark::Check(n);printf(ok?"c512 wave qkv matches\n":"c512 wave qkv MISMATCH\n");return ok?0:1;
}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}

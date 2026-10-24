#define DLSS5_LAYER_BENCH 1
#include "hip_reference_network.h"
#include <cmath>
namespace hip_reference { struct LayerBenchmark {
static bool Check(Network&n,U block,U tokens,U pattern){
 std::vector<float>v(size_t(tokens)*1024);for(size_t i=0;i<v.size();i++)v[i]=pattern==0?0.f:float(int((i*73)%2048)-1024)/(pattern==1?512.f:8192.f);
 auto in=n.Upload(v.data(),v.size()*4),q=n.New(size_t(tokens)*3072),a=n.New(size_t(tokens)*3072),b=n.New(size_t(tokens)*3072);auto w=n.Weight(n.Block(block,"qkv"));
 n.Run("deep","vit_qkv_project_blocked",size_t(tokens)*3072,n.P(in),w,n.P(q),tokens);
 n.Run("deep","vit_qkv_normalize",size_t(tokens)*96,n.P(q),w,n.P(a),tokens);
 n.Run("deep","vit_qkv_project_normalize_fused",size_t(tokens)*3072,n.P(in),w,n.P(b),tokens);n.Synchronize();
 std::vector<float>x(size_t(tokens)*3072),y(x.size());n.api.Check(n.api.hipMemcpy(x.data(),n.P(a),x.size()*4,2),"read original");n.api.Check(n.api.hipMemcpy(y.data(),n.P(b),y.size()*4,2),"read fused");size_t diff=0,bad=0;for(size_t i=0;i<x.size();i++){diff+=memcmp(&x[i],&y[i],4)!=0;bad+=!std::isfinite(x[i])||!std::isfinite(y[i]);}printf("block=%u tokens=%u pattern=%u bitdiff=%zu invalid=%zu\n",block,tokens,pattern,diff,bad);return !diff&&!bad;
}}; }
int main(int argc,char**argv){try{if(argc!=3)throw std::runtime_error("test_vit_qkv ASSETS MODULES");hip_reference::Options o;o.assets=argv[1];o.modules=argv[2];o.fast_deep=o.packed_weights=true;hip_reference::Network n(o);bool ok=true;for(unsigned block=31;block<=38;block++)for(unsigned pattern=0;pattern<3;pattern++)ok=hip_reference::LayerBenchmark::Check(n,block,32,pattern)&&ok;return ok?0:1;}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 2;}}

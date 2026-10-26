#include "hip_reference_network.h"
#include <fstream>
int main(int argc,char**argv){using namespace hip_reference;std::string assets=argv[1],out=argv[2];
 auto save=[&](std::string n,const std::vector<float>&v){std::ofstream f(out+"/"+n,std::ios::binary);f.write((char*)v.data(),v.size()*4);};
 for(std::string prefix:{"block0","block1","block4","block66","block69","post70"})for(bool attention:{false,true}){
  std::string name=prefix+(attention?"-attention.f32":"-ffn.f32");auto v=ReadWeights(assets+"/"+name);
  if(attention){PackWeightRegions(v,{{0,4096}});FragmentPackedMatrixW16(v,0,96,32);FragmentPackedMatrixW16(v,768,32,32);}
  else{PackWeightRegions(v,{{512,4096},{4608,4096}});FragmentPackedMatrixW16(v,512,128,32);FragmentPackedMatrixW16(v,4608,32,128);AppendC32ResidualDiagonalsW16(v);}
  save(name+".v2.bin",v);AppendC32AmpereHalfWeights(v,attention);save(name+".v3.bin",v);
 }
 for(std::string n:{"post70-scales.f32","post70-head.f32"})save(n+".bin",ReadWeights(assets+"/"+n));
 auto up=ReadWeights(assets+"/block66-weights.f32");PackHalfMatrixRounded(up,0,2048);save("up.bin",up);
}

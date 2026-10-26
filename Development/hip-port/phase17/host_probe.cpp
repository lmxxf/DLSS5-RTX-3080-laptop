#include "packed_weights.h"
#include <fstream>
#include <iostream>
int main(int argc,char**argv){using namespace hip_reference;std::string dir=argv[1];
 std::ofstream table(dir+"/half-table.bin",std::ios::binary);for(unsigned i=0;i<256;i++){uint16_t x=AmpereFp8HalfBits(uint8_t(i));table.write((char*)&x,2);}
 for(bool attention:{false,true}){
  const size_t old=attention?32900:41088;std::vector<float>v(old/4,.1234567f);auto*bytes=(uint8_t*)v.data();
  auto regions=attention?std::vector<std::pair<size_t,size_t>>{{0,4096}}:std::vector<std::pair<size_t,size_t>>{{2048,4096},{18432,4096},{34944,1536}};
  for(auto r:regions)for(size_t i=0;i<r.second;i++)bytes[r.first+i]=uint8_t(i*37+i/256);
  const std::vector<float>original=v;AppendC32AmpereHalfWeights(v,attention);if(std::memcmp(original.data(),v.data(),old))return 1;
  const auto*h=(const uint16_t*)((uint8_t*)v.data()+(attention?32912:41088));size_t n=0;
  for(auto r:regions)for(size_t i=0;i<r.second;i++)if(h[n++]!=AmpereFp8HalfBits(((const uint8_t*)original.data())[r.first+i]))return 2;
  std::cout<<"append attention="<<attention<<" old="<<old<<" new="<<v.size()*4<<" half_elements="<<n<<" old_bytes_unchanged=1\n";
 }
 return 0;
}

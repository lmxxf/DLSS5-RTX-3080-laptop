#include "packed_weights.h"
#include <cmath>
#include <cstdio>
using namespace hip_reference;
static float decode(unsigned b){unsigned e=(b>>3)&15,m=b&7;float v=e?std::ldexp(1.f+m/8.f,int(e)-7):m/512.f;return b&128?-v:v;}
int main(){for(unsigned b=0;b<256;b++)if((b&127)!=127&&ExactWeightFp8(decode(b))!=b)return 1;
 for(float x:{.1f,449.f,INFINITY,NAN,1.e-10f}){bool rejected=false;try{ExactWeightFp8(x);}catch(...){rejected=true;}if(!rejected)return 2;}
 std::vector<float> v(160);for(unsigned i=0;i<v.size();i++)v[i]=decode(i%127);auto original=v;PackWeightRegions(v,{{0,32},{48,64}});auto*b=reinterpret_cast<const uint8_t*>(v.data());auto*old=reinterpret_cast<const uint8_t*>(original.data());for(size_t i=0;i<v.size()*4;i++){bool packed=i<32||(i>=48*4&&i<48*4+64);if(!packed&&b[i]!=old[i])return 3;}for(unsigned i=0;i<32;i++)if(b[i]!=ExactWeightFp8(original[i]))return 4;for(unsigned i=0;i<64;i++)if(b[48*4+i]!=ExactWeightFp8(original[48+i]))return 5;
 bool rejected=false;try{PackWeightRegions(v,{{10,30},{20,30}});}catch(...){rejected=true;}if(!rejected)return 6;puts("PASS finite E4M3 roundtrip, rejection, matrix regions and untouched f32 fields");}

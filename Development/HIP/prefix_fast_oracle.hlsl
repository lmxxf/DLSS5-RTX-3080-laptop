// Literal production ff n_fused mode5 prefix, stopped before FFN; diagnostic stores only.
#include <dx/linalg.h>
ByteAddressBuffer ffn_weights:register(t0),ffn_input:register(t1),ffn_coeff:register(t3);
RWByteAddressBuffer output:register(u0);
cbuffer Runtime:register(b0){uint runtime_seed;uint runtime_width;uint runtime_height;uint local_oracle;uint temporal_enabled;}
groupshared float16_t ex[512];
using A=dx::linalg::Matrix<dx::linalg::ComponentType::F16,16,32,dx::linalg::MatrixUse::A,dx::linalg::MatrixScope::Wave>;
using B=dx::linalg::Matrix<dx::linalg::ComponentType::F16,32,16,dx::linalg::MatrixUse::B,dx::linalg::MatrixScope::Wave>;
using C=dx::linalg::Matrix<dx::linalg::ComponentType::F32,16,16,dx::linalg::MatrixUse::Accumulator,dx::linalg::MatrixScope::Wave>;
uint ffn_pcg(uint s){uint w=((s>>((s>>28)+4))^s)*0x108ef2d9;return (w>>22)^w;}
float ffn_uniform24(uint s){uint w=((s>>((s>>28)+4))^s)*0x108ef2d9;return float(((w>>30)^(w>>8))+1)*5.9604644775390625e-8;}
float ffn_half_round(float v){return f16tof32(f32tof16(v));}
[WaveSize(32)] [numthreads(32,1,1)] void main(uint3 gid:SV_GroupID,uint t:SV_GroupIndex){uint first=gid.x*16,ebase=0;if(first>=runtime_width*runtime_height)return;C in0,in1;
  if(t<16){
   const uint p=first+t;
   uint x=p%8,y=(p/8)%8;
   if(!local_oracle){uint tile=p/64;x=(tile%(runtime_width/8))*8+p%8;y=(tile/(runtime_width/8))*8+(p%64)/8;}
   uint h=ffn_pcg((x*0x8da6b343)^(y*0xd8163841)^(runtime_seed*0x9e3779b9u)^0x243f6a88u);
   float a=ffn_uniform24(h*0xcaa5b80d+0x21dd796b),b=ffn_uniform24(h*0x2c9277b5+0xac564b05);
   float c=ffn_uniform24(h*0x83232c31+0x3463e0ac),d=ffn_uniform24(h*0xfa6dc5f9+0x4712a88e);
   float r0=sqrt(-2*log(a)),r1=sqrt(-2*log(b));
   float g0=ffn_half_round(r0*cos(6.283185482025146*c)),g1=ffn_half_round(r1*cos(6.283185482025146*d)),g2=ffn_half_round(r1*sin(6.283185482025146*d));
   float r=ffn_half_round(ffn_half_round(ffn_half_round(asfloat(ffn_input.Load(p*16)))-0.5)*.125),g=ffn_half_round(ffn_half_round(ffn_half_round(asfloat(ffn_input.Load(p*16+4)))-0.5)*.125),bl=ffn_half_round(ffn_half_round(ffn_half_round(asfloat(ffn_input.Load(p*16+8)))-0.5)*.125);
   float features[16]={g1,g2,g,bl,g0,1,.0078125,1,r,g,1,1,bl,r,1,0};
   if(temporal_enabled){uint tile=p/64;uint tx=(tile%(runtime_width/8))*8+p%8,ty=(tile/(runtime_width/8))*8+(p%64)/8;float3 hist=asfloat(ffn_coeff.Load3((ty*runtime_width+tx)*16));
    features[13]=ffn_half_round(ffn_half_round(ffn_half_round(hist.x)-.5)*.125);features[2]=ffn_half_round(ffn_half_round(ffn_half_round(hist.y)-.5)*.125);features[3]=ffn_half_round(ffn_half_round(ffn_half_round(hist.z)-.5)*.125);}
   [unroll]for(uint i=0;i<16;i++)ex[ebase+t*32+i]=float16_t(features[i]);
   [unroll]for(uint i=16;i<32;i++)ex[ebase+t*32+i]=float16_t(0.0);
  }
  GroupMemoryBarrier();
  for(uint i=t;i<512;i+=32)output.Store((runtime_width*runtime_height*32+first*32+i)*4,asuint(float(ex[i])));
  A fa=A::Load(ex,ebase,32,dx::linalg::MatrixLayout::RowMajor);
  B b0=B::Load(ffn_weights,27776,32,dx::linalg::MatrixLayout::RowMajor,16),b1=B::Load(ffn_weights,27776+1024,32,dx::linalg::MatrixLayout::RowMajor,16);
  in0=dx::linalg::Multiply<dx::linalg::ComponentType::F32>(fa,b0);in1=dx::linalg::Multiply<dx::linalg::ComponentType::F32>(fa,b1);
  for(uint i=0;i<in0.Length();i++){in0.Set(i,ffn_half_round(in0.Get(i)));in1.Set(i,ffn_half_round(in1.Get(i)));}
 in0.Store(output,first*128,128,dx::linalg::MatrixLayout::RowMajor,16);in1.Store(output,first*128+64,128,dx::linalg::MatrixLayout::RowMajor,16);
}

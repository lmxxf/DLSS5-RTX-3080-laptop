using U=unsigned;
SM86_DEV float p14_h(U h){return float(__builtin_bit_cast(_Float16,(unsigned short)h));}
SM86_DEV void p14_pack(sm86_i2& a,U e,float v){U b=(U)__builtin_amdgcn_cvt_pk_fp8_f32(v,0.f,0,false)&255u;a[e/4]=(int)((U)a[e/4]|(b<<(8*(e%4))));}
extern "C" __attribute__((global)) void layout(const unsigned char*in,float*out,U mode){
 U lane=sm86_lane_id(),r=lane&15,g=lane>>4;sm86_i2 q[2]{};sm86_f8 a{};
 for(U k=0;k<32;k+=16){__builtin_memcpy(&q[k/16],in+r*32+k+g*8,8);sm86_i2 y{};__builtin_memcpy(&y,in+(16+r)*32+k+g*8,8);if(mode&1)q[k/16]=sm86_preshuffle_fp8(q[k/16]);a=(mode&1)&&(mode&4)?sm86_wmma_fp8_preshuffled_a(q[k/16],y,a):__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(q[k/16],y,a);}
 __attribute__((shared)) unsigned short t16[16*24];
 for(U e=0;e<8;e++){
  float af=a[e]*p14_h(0x2dbb)+1.708984375f;af=af<1.439453125f?1.439453125f:af>1.9775390625f?1.9775390625f:af;
  U hb=(__builtin_bit_cast(U,af)>>13)-0x1c000u;unsigned short u=(unsigned short)(((hb<<4)+0x4000u)&65535u);
  t16[(g*8+e)*24+r]=u;out[lane*48+e]=a[e];out[lane*48+8+e]=p14_h(u);
 }
 __builtin_amdgcn_s_barrier();
 sm86_h8 x{},ones{};sm86_i2 xb{};
 for(U e=0;e<8;e++){unsigned short u=t16[r*24+g*8+e];x[e]=__builtin_bit_cast(_Float16,u);ones[e]=(_Float16)1;p14_pack(xb,e,p14_h(u));out[lane*48+16+e]=p14_h(u);}
 if(mode&2)xb=sm86_preshuffle_fp8(xb);
 sm86_f8 sum=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(x,ones,sm86_f8{});
 for(U c=0;c<2;c++){sm86_i2 y{};for(U e=0;e<8;e++){U b=in[(32+g*8+e)*32+c*16+r];y[e/4]=(int)((U)y[e/4]|(b<<(8*(e%4))));}sm86_f8 av=(mode&2)&&(mode&4)?sm86_wmma_fp8_preshuffled_a(xb,y,sm86_f8{}):__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(xb,y,sm86_f8{});
  for(U e=0;e<8;e++)out[lane*48+32+c*8+e]=av[e];}
 for(U e=0;e<8;e++)out[lane*48+24+e]=sum[e];
}

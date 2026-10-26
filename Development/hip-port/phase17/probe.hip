#include PHASE17_HEADER
using U=unsigned;
extern "C" __attribute__((global)) void decode(const unsigned char*bytes,const unsigned char*half,U*out,U count){
 U i=__builtin_amdgcn_workgroup_id_x()*32+sm86_lane_id();if(i>=count)return;
 sm86_i2 a;__builtin_memcpy(&a,bytes+i*8,8);sm86_u4 x=__sm86_unpack_fp8(a),y=cw_half_load({half+i*16});
 _Pragma("unroll") for(U k=0;k<4;k++){out[i*8+k]=x[k];out[i*8+4+k]=y[k];}
}
extern "C" __attribute__((global)) void mma(const unsigned char*bytes,const unsigned char*half,const unsigned char*dynamic,const float*c,float*out,U count){
 U i=__builtin_amdgcn_workgroup_id_x()*32+sm86_lane_id();if(i>=count)return;
 sm86_i2 a,b;__builtin_memcpy(&a,bytes+i*8,8);__builtin_memcpy(&b,dynamic+i*8,8);sm86_f8 olda,newa,oldb,newb;
 _Pragma("unroll") for(U e=0;e<8;e++)olda[e]=newa[e]=oldb[e]=newb[e]=c[i*8+e];
 _Pragma("unroll") for(U step=0;step<4;step++){
 olda=sm86_wmma_fp8_preshuffled_ab(a,b,olda);newa=sm86_c32_half_a({half+i*16},b,newa);
 oldb=sm86_wmma_fp8_preshuffled_ab(b,a,oldb);newb=sm86_c32_half_b(b,{half+i*16},newb);}
 _Pragma("unroll") for(U e=0;e<8;e++){out[i*32+e]=olda[e];out[i*32+8+e]=newa[e];out[i*32+16+e]=oldb[e];out[i*32+24+e]=newb[e];}
}

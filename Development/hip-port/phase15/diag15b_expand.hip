#pragma clang fp contract(off)
#pragma clang fp reassociate(off)
using U=unsigned;
extern "C" __attribute__((global)) void expand_canonical(const unsigned char*x,const unsigned char*w,float*raw,unsigned char*out,U tokens){
 U lane=sm86_lane_id(),r=lane&15,g=lane>>4,bid=__builtin_amdgcn_workgroup_id_x(),first=(bid/256)*16,col=(bid%256)*16;if(first>=tokens)return;sm86_f8 c{};
 for(U k=0;k<1024;k+=16){sm86_i2 a{},b{};__builtin_memcpy(&a,x+(first+r)*1024+k+g*8,8);__builtin_memcpy(&b,w+(col+r)*1024+k+g*8,8);c=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,c);}
 for(U e=0;e<8;e++){U pos=(first+g*8+e)*4096+col+r;float v=c[e];raw[pos]=v;float z=v<-4?-4:v>4?4:v;float poly=__builtin_fmaf(z,__builtin_fmaf(__builtin_fabsf(z),-.055908203125f,.447265625f),.89453125f);float value=v*poly;asm("add.rn.f32 %0,%1,0f00000000;":"=f"(value):"f"(value));value=value<-448?-448:value>448?448:value;out[pos]=(unsigned char)(__builtin_amdgcn_cvt_pk_fp8_f32(value,0.f,0,false)&255);}
}

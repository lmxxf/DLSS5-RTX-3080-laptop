using U=unsigned;
extern "C" __attribute__((global)) void half_pack(const unsigned short* in,U* out,U n){
 U batch=__builtin_amdgcn_workgroup_id_x(),lane=sm86_lane_id();if(batch>=n)return;
 sm86_h8 h;_Pragma("unroll") for(U e=0;e<8;e++)h[e]=__builtin_bit_cast(_Float16,in[(batch*32+lane)*8+e]);
 sm86_f8 f=__builtin_convertvector(h,sm86_f8);U lo=0,hi=0;
 _Pragma("unroll") for(U e=0;e<8;e++){U q=sm86_f32_to_e4m3_byte(f[e]);if(e<4)lo|=q<<(8*e);else hi|=q<<(8*(e-4));}
 sm86_i2 got=sm86_pack_half_h8_e4m3(h);out[(batch*32+lane)*4]=lo;out[(batch*32+lane)*4+1]=hi;out[(batch*32+lane)*4+2]=got[0];out[(batch*32+lane)*4+3]=got[1];
}

extern "C" __attribute__((global)) void half_pack_rtz(const unsigned short* in,U* out,U n){
 U batch=__builtin_amdgcn_workgroup_id_x(),lane=sm86_lane_id();if(batch>=n)return;
 sm86_h8 h;_Pragma("unroll") for(U e=0;e<8;e++)h[e]=__builtin_bit_cast(_Float16,in[(batch*32+lane)*8+e]);
 sm86_u4 rounded;_Pragma("unroll") for(U j=0;j<4;j++)rounded[j]=sm86_v_cvt_pkrtz_f16_f32(float(h[j*2]),float(h[j*2+1]));h=__builtin_bit_cast(sm86_h8,rounded);
 sm86_f8 f=__builtin_convertvector(h,sm86_f8);U lo=0,hi=0;
 _Pragma("unroll") for(U e=0;e<8;e++){U q=sm86_f32_to_e4m3_byte(f[e]);if(e<4)lo|=q<<(8*e);else hi|=q<<(8*(e-4));}
 sm86_i2 got=sm86_pack_half_h8_e4m3(h);out[(batch*32+lane)*4]=lo;out[(batch*32+lane)*4+1]=hi;out[(batch*32+lane)*4+2]=got[0];out[(batch*32+lane)*4+3]=got[1];
}

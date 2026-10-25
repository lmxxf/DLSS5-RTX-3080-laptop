using U=unsigned;
extern "C" __attribute__((global)) void half_store(const unsigned short* in,U* out,U n){
 U batch=__builtin_amdgcn_workgroup_id_x(),lane=sm86_lane_id();if(batch>=n)return;
 sm86_h8 h;_Pragma("unroll") for(U e=0;e<8;e++)h[e]=__builtin_bit_cast(_Float16,in[(batch*32+lane)*8+e]);
 sm86_f8 f=__builtin_convertvector(h,sm86_f8);sm86_u4 got=__builtin_bit_cast(sm86_u4,__builtin_convertvector(f,sm86_h8));
 _Pragma("unroll") for(U j=0;j<4;j++){U old=sm86_v_cvt_pkrtz_f16_f32(f[j*2],f[j*2+1]);out[(batch*32+lane)*8+j]=old;out[(batch*32+lane)*8+4+j]=got[j];}
}

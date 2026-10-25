using U=unsigned;
extern "C" __attribute__((global)) void compare_layouts(const U* cbits,const U* dbits,U* out,U count){
 U batch=__builtin_amdgcn_workgroup_id_x(),lane=sm86_lane_id();if(batch>=count)return;
 sm86_f8 c;sm86_u4 d;
 _Pragma("unroll") for(U e=0;e<8;e++)c[e]=__builtin_bit_cast(float,cbits[(batch*32+lane)*8+e]);
 _Pragma("unroll") for(U e=0;e<4;e++)d[e]=dbits[(batch*32+lane)*4+e];
 sm86_f8 cf=__sm86_c_to_ampere_f32(c);
 sm86_u4 cr={sm86_pack_acc(cf[0],cf[1]),sm86_pack_acc(cf[2],cf[3]),sm86_pack_acc(cf[4],cf[5]),sm86_pack_acc(cf[6],cf[7])};
 sm86_u4 cn=__sm86_c_to_ampere(c);
 sm86_f8 dr=__sm86_d_to_rdna4_f32(sm86_unpack_acc(d)),dn=__sm86_d_to_rdna4(d);
 _Pragma("unroll") for(U e=0;e<4;e++){out[(batch*32+lane)*24+e]=cr[e];out[(batch*32+lane)*24+4+e]=cn[e];}
 _Pragma("unroll") for(U e=0;e<8;e++){out[(batch*32+lane)*24+8+e]=__builtin_bit_cast(U,dr[e]);out[(batch*32+lane)*24+16+e]=__builtin_bit_cast(U,dn[e]);}
}

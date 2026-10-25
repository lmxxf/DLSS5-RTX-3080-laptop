using U=unsigned;
extern "C" __attribute__((global)) void sequence(const U*in,U*out){
 U w=__builtin_amdgcn_workgroup_id_x(),l=sm86_lane_id();sm86_u4 old0{},old1{},new0{},new1{};
 for(U h=0;h<4;h++){
  sm86_u4 a[2],b[2][2];
  _Pragma("unroll") for(U hp=0;hp<2;hp++){
   _Pragma("unroll") for(U e=0;e<4;e++)a[hp][e]=in[(((w*4+h)*32+l)*24)+hp*4+e];
   _Pragma("unroll") for(U ci=0;ci<2;ci++)_Pragma("unroll") for(U e=0;e<4;e++)b[ci][hp][e]=in[(((w*4+h)*32+l)*24)+8+(ci*2+hp)*4+e];
  }
  old0=sm86_mma_prepared_core(b[0][0],a[0],old0);old0=sm86_mma_prepared_core(b[0][1],a[1],old0);
  old1=sm86_mma_prepared_core(b[1][0],a[0],old1);old1=sm86_mma_prepared_core(b[1][1],a[1],old1);
  new0=sm86_mma_prepared_core(b[0][0],a[0],new0);new1=sm86_mma_prepared_core(b[1][0],a[0],new1);
  new0=sm86_mma_prepared_core(b[0][1],a[1],new0);new1=sm86_mma_prepared_core(b[1][1],a[1],new1);
 }
 _Pragma("unroll") for(U e=0;e<4;e++){out[(w*32+l)*16+e]=old0[e];out[(w*32+l)*16+4+e]=old1[e];out[(w*32+l)*16+8+e]=new0[e];out[(w*32+l)*16+12+e]=new1[e];}
}

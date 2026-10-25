using U=unsigned;
extern "C" __attribute__((global)) void permute(const U* orig,const U* packed,U* out,U count){
 U batch=__builtin_amdgcn_workgroup_id_x(),l=sm86_lane_id();if(batch>=count)return;
 sm86_i2 a={(int)orig[batch*64+l*2],(int)orig[batch*64+l*2+1]},b={(int)packed[batch*64+l*2],(int)packed[batch*64+l*2+1]};
 sm86_u4 ref=__sm86_prep_fp8(a),got=__sm86_unpack_fp8(b);sm86_i2 pre=sm86_preshuffle_fp8(a);
 _Pragma("unroll") for(U e=0;e<4;e++){out[(batch*32+l)*10+e]=ref[e];out[(batch*32+l)*10+4+e]=got[e];}
 out[(batch*32+l)*10+8]=pre[0];out[(batch*32+l)*10+9]=pre[1];
}
extern "C" __attribute__((global)) void ones(const unsigned short* hx,const float* c,float* out,U count){
 U batch=__builtin_amdgcn_workgroup_id_x(),l=sm86_lane_id();if(batch>=count)return;
 sm86_h8 x,one;sm86_f8 ar,br,an,bn;
 _Pragma("unroll") for(U e=0;e<8;e++){x[e]=__builtin_bit_cast(_Float16,hx[(batch*32+l)*8+e]);one[e]=(_Float16)1;ar[e]=br[e]=an[e]=bn[e]=c[(batch*32+l)*8+e];}
 _Pragma("unroll") for(U k=0;k<4;k++){
 ar=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(one,x,ar);an=sm86_wmma_ones_a(x,an);
 br=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(x,one,br);bn=sm86_wmma_ones_b(x,bn);
 _Pragma("unroll") for(U e=0;e<8;e++){out[(((batch*4+k)*4+0)*32+l)*8+e]=ar[e];out[(((batch*4+k)*4+1)*32+l)*8+e]=an[e];out[(((batch*4+k)*4+2)*32+l)*8+e]=br[e];out[(((batch*4+k)*4+3)*32+l)*8+e]=bn[e];}}
}
extern "C" __attribute__((global)) void packed_add(const U* a,const U* b,U* out,U count){
 U batch=__builtin_amdgcn_workgroup_id_x(),l=sm86_lane_id();if(batch>=count)return;sm86_u4 x,y;
 _Pragma("unroll") for(U j=0;j<4;j++){x[j]=a[(batch*32+l)*4+j];y[j]=b[(batch*32+l)*4+j];}
 sm86_f8 xf=sm86_unpack_acc(x),yf=sm86_unpack_acc(y);sm86_u4 d=sm86_add_u4_f16x2(x,y);
 _Pragma("unroll") for(U j=0;j<4;j++){out[(batch*32+l)*8+j]=d[j];out[(batch*32+l)*8+4+j]=sm86_pack_acc(xf[j*2]+yf[j*2],xf[j*2+1]+yf[j*2+1]);}
}
// A concrete non-associativity check for seeding a partial dot with the running total.
extern "C" __attribute__((global)) void seeded_partition_counterexample(float* out,U count){
 U l=sm86_lane_id();sm86_h8 a,n,b;sm86_f8 total;
 _Pragma("unroll") for(U e=0;e<8;e++){a[e]=(_Float16)128;n[e]=(_Float16)-128;b[e]=(_Float16)1;total[e]=1;}
 sm86_f8 partial=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(a,b,sm86_f8{});
 partial=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(n,b,partial);
 sm86_f8 separate=__sm86_d_to_rdna4(sm86_add_u4_f16x2(__sm86_c_to_ampere(total),__sm86_c_to_ampere(partial)));
 sm86_f8 seeded=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(a,b,total);
 seeded=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(n,b,seeded);
 _Pragma("unroll") for(U e=0;e<8;e++){out[l*16+e]=separate[e];out[l*16+8+e]=seeded[e];}
}

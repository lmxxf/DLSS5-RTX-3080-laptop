// 2026-09-17 experiment: one work-group per 8x8 window does the whole C64 block — FFN + projection + QKV + normalization for its
// 64 tokens (the mh_ffn_fused_c64_project[_mapped]_g128_qkv body, two 16-token groups at a time on the 8 waves) and then the
// attention + residual + output projection (the c64_attention_project_diag body) on the normalized Q/K/V and feature bytes kept
// in LDS. Nothing changes arithmetically: every token's FFN/QKV is the same instruction sequence in the same wave/lane layout,
// and the attention phase reads the same bytes it used to read from global memory. What disappears per block is the write and
// re-read of the normalized stream (n*192 B) and the feature (n*256 B f32), plus one launch. Built after multihead_fast_padded.hip
// (module c64-window-fused: HIP_ISA_HALF 1, HIP_PREPACKED_WEIGHTS 1, HIP_FFN_HOIST_RES 2); host option mh_window_fused.
// Weights: fw = PackedFusedMhWeight(ffn), aw = PackedMhWeightDiag(attention) (same E4M3 prefix as PackedMhWeight(...,true); the
// residual diagonals follow). Feature bytes: the production f32 feature is the E4M3 lattice value, so fp8(feature) == byte.
DEV uint wf_rc(){return __builtin_amdgcn_workitem_id_x()&15;}
DEV uint wf_gr(){return (__builtin_amdgcn_workitem_id_x()&31)>>4;}
DEV uint wf_raster(uint win,uint tok,uint width){return ((win/(width/8))*8+tok/8)*width+(win%(width/8))*8+tok%8;}
DEV void wf_sync(){__builtin_amdgcn_fence(3,"workgroup");__builtin_amdgcn_s_barrier();__builtin_amdgcn_fence(2,"workgroup");}
DEV uint wf_fp8(float f){return uint(__builtin_amdgcn_cvt_pk_fp8_f32(__builtin_fminf(__builtin_fmaxf(f,-448.f),448.f),0.f,0,false))&255u;}
DEV void wf_put_bits(i2&v,uint e,uint b){v[e/4]=int(uint(v[e/4])|((b&255u)<<(8*(e%4))));}
using wf_ushort=unsigned short;

template<bool Mapped,bool ByteIn,bool ByteOut>
DEV void c64_window_body(const float*in,const float*fw,const float*aw,void*out_any,uint width,uint height,uint workw,uint workh,uint sx,uint sy,uint post,uint crop){
 constexpr uint C=64;
 const unsigned char*in8=reinterpret_cast<const unsigned char*>(in);
 float*out=static_cast<float*>(out_any);unsigned char*out8=static_cast<unsigned char*>(out_any);
 uint windows=(workw/8)*(workh/8),win=__builtin_amdgcn_workgroup_id_x();if(workw%8||workh%8||win>=windows)return;
 uint alltid=__builtin_amdgcn_workitem_id_x(),grp=alltid/128,tid0=alltid%128,wave0=tid0/32,l=tid0%32,rc0=l&15,group0=l>>4;
 // LDS: normalized Q/K/V bytes [tok][3][64], feature bytes [tok][64], and the phase scratch (FFN staging of two token groups,
 // then the attention's ex/packed region).
 __attribute__((shared)) unsigned char nrm[64*3*C];
 __attribute__((shared)) unsigned char feat[64*C];
 union FfnStorage{unsigned char bytes[16*(4*C+4)];float raw[16*(C/32)*33];};
 struct FfnPhase{FfnStorage storage[2];unsigned char qfeature[2][16*(C+4)];float inverse[2][16*(C/32)];};
 struct AttnPhase{_Float16 ex[2*64*66];unsigned char packed[2*64*36];};
 union Scratch{FfnPhase ffn;AttnPhase attn;};
 __attribute__((shared)) Scratch scratch;
 const uint*pw=reinterpret_cast<const uint*>(fw);
 const uint*aq=reinterpret_cast<const uint*>(aw);
 // ---- phase 1: FFN + projection + QKV + normalization, token groups (pass*2+grp) of 16 window tokens on waves grp*4..grp*4+3.
#ifndef HIP_WF_PHASE
#define HIP_WF_PHASE 0 /* diagnostic: 1 = compile phase 1 only, 2 = phase 2 only (register pressure per phase) */
#endif
#if HIP_WF_PHASE!=2
#ifndef HIP_WF_UNROLL_PASS
#define HIP_WF_UNROLL_PASS 0 /* 1: let the compiler unroll the two token-group passes (keeps the weight fragments of both passes live: VGPR 196, occupancy 6) */
#endif
#if !HIP_WF_UNROLL_PASS
 _Pragma("clang loop unroll(disable)")
#endif
#ifndef HIP_WF_PASSES
#define HIP_WF_PASSES 2 /* diagnostic only: 1 = a single token-group pass (wrong output, register pressure of the loop form) */
#endif
 for(uint pass=0;pass<HIP_WF_PASSES;pass++){
  const uint g=pass*2+grp;
  uint tid=tid0,wave=wave0,rc=rc0,group=group0;
#if !HIP_WF_UNROLL_PASS
  /* Launder the lane coordinates per pass: every weight-fragment address below derives from them, so none is loop-invariant and
     LICM cannot keep both passes' 64-bit address pairs live across the loop (that form: VGPR 193 for this phase, 96 standalone). */
  __asm__ volatile("" : "+v"(tid),"+v"(wave),"+v"(rc),"+v"(group));
#endif
  unsigned char*hidden=scratch.ffn.storage[grp].bytes;float*raw=scratch.ffn.storage[grp].raw;unsigned char*qfeature=scratch.ffn.qfeature[grp];float*inverse=scratch.ffn.inverse[grp];
  auto P=[&](uint row)->uint{return wf_raster(win,g*16+row,workw);};
  auto load_in_nb=[&](uint row,uint k)->float{if constexpr(ByteIn)return ffn_input8_nb<C,Mapped>(in8,P(row),k,width,height,workw,sx,sy);else return ffn_input_nb<C,Mapped>(in,P(row),k,width,height,workw,sx,sy);};
  for(uint i=tid;i<16*(C/4+1);i+=2*C){uint row=i/(C/4+1),k=(i%(C/4+1))*4,word=0;if(k<C)word=pack4(load_in_nb(row,k),load_in_nb(row,k+1),load_in_nb(row,k+2),load_in_nb(row,k+3));__builtin_memcpy(hidden+i*4,&word,4);}
  __builtin_amdgcn_s_barrier();
  f8 expand[4]{};
  for(uint k=0;k<C;k+=16){i2 a{};__builtin_memcpy(&a,hidden+rc*(C+4)+k+group*8,8);
   for(uint tile=0;tile<4;tile++){uint row=wave*64+tile*16+rc,offset=(row*C+k+group*8)/4;i2 b={int(pw[offset]),int(pw[offset+1])};expand[tile]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,expand[tile]);}
  }
  __builtin_amdgcn_s_barrier();
  for(uint tile=0;tile<4;tile++)for(uint e=0;e<8;e++){float a=expand[tile][e],gg=clampf(a,-4.f,4.f),q=absf(gg)*(-.055908203125f)+.447265625f,poly=gg*q+.89453125f;hidden[(group*8+e)*(4*C+4)+wave*64+tile*16+rc]=static_cast<unsigned char>(q8_fused_round(a*poly));}
  __builtin_amdgcn_s_barrier();
  f8 accum{};
  const uint first_k=(wave/2)*128,last_k=first_k+128;
  for(uint k=first_k;k<last_k;k+=16){i2 a;__builtin_memcpy(&a,hidden+rc*(4*C+4)+k+group*8,8);uint offset=4*C*C+((wave*16+rc)*(4*C)+k+group*8)/4;i2 b={int(pw[offset]),int(pw[offset+1])};accum=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,accum);}
  __builtin_amdgcn_s_barrier();
  for(uint e=0;e<8;e++)hidden[(group*8+e)*(C+4)+wave*16+rc]=static_cast<unsigned char>(q8_fused_round(Hrtz(accum[e])));
  __builtin_amdgcn_s_barrier();
  f8 result{};{const float rs=fw[9*C*C+wave*16+rc];float rv[8];
   for(uint e=0;e<8;e++)rv[e]=load_in_nb(group*8+e,wave*16+rc);
   for(uint e=0;e<8;e++)result[e]=Hrtz(rv[e]*rs);}
  for(uint k=0;k<C;k+=16){i2 a,b;__builtin_memcpy(&a,hidden+rc*(C+4)+k+group*8,8);uint off=8*C*C+((wave*16+rc)*C+k+group*8)/4;b={int(pw[off]),int(pw[off+1])};result=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,result);}
  for(uint e=0;e<8;e++){uint byte=q8_fused_round(result[e]);feat[(g*16+group*8+e)*C+wave*16+rc]=static_cast<unsigned char>(byte);qfeature[(group*8+e)*(C+4)+wave*16+rc]=static_cast<unsigned char>(byte);}
  __builtin_amdgcn_s_barrier();
  for(uint part=0;part<3;part++){f8 q{};
   for(uint k=0;k<C;k+=16){i2 a,b;__builtin_memcpy(&a,qfeature+rc*(C+4)+k+group*8,8);uint off=((part*C+wave*16+rc)*C+k+group*8)/4;b={int(aq[off]),int(aq[off+1])};q=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,q);}
   if(part<2){for(uint e=0;e<8;e++)raw[((wave/2)*16+group*8+e)*33+(wave%2)*16+rc]=q[e];
    __builtin_amdgcn_s_barrier();
    if(tid<16*(C/32)){uint head=tid/16,row=tid%16;float ss=0;for(uint k=0;k<32;k++){float v=raw[(head*16+row)*33+k];ss+=v*v;}inverse[tid]=__builtin_amdgcn_rsqf(maxf(ss,6.198883056640625e-5f))*(part==0?aw[4*C*C+(C/32)*4096+head]:1.f);}
    __builtin_amdgcn_s_barrier();
   }
   for(uint e=0;e<8;e++){uint row=group*8+e;float inv=part<2?inverse[(wave/2)*16+row]:1.f;nrm[((g*16+row)*3+part)*C+wave*16+rc]=static_cast<unsigned char>(q8_fused_round(q[e]*inv));}
  }
  __builtin_amdgcn_s_barrier();
 }
#endif
 wf_sync();
 // ---- phase 2: c64_attention_project_body<ByteFeature=true,ByteOut,Diag=true> on the window's LDS bytes.
#if HIP_WF_PHASE!=1
 {
 const uint channels=64;
 uint head=alltid/128,atid=alltid%128,awave=atid/32,first=awave*16;
 _Float16*ex=scratch.attn.ex+head*64*66;unsigned char*packed=scratch.attn.packed+head*64*36;
 unsigned char*avbytes=reinterpret_cast<unsigned char*>(scratch.attn.ex);
 for(uint i=atid;i<64*8;i+=128){uint tok=i/8,c=(i%8)*4,word;__builtin_memcpy(&word,nrm+(tok*3+2)*channels+head*32+c,4);__builtin_memcpy(packed+tok*36+c,&word,4);}
 wf_sync();
 for(uint key=0;key<64;key+=16){f8 acc{};
  for(uint kt=0;kt<2;kt++){i2 a{},b{};uint qp=first+wf_rc(),kp=key+wf_rc(),off=kt*16+wf_gr()*8;__builtin_memcpy(&a,nrm+qp*3*channels+head*32+off,8);__builtin_memcpy(&b,nrm+(kp*3+1)*channels+head*32+off,8);acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,acc);}
  for(uint e=0;e<8;e++){uint q=first+wf_gr()*8+e,k=key+wf_rc();float score=acc[e]+aw[4*channels*channels+head*4096+q*64+k],affine=clampf(score*.044921875f+1.30078125f,1.03125f,1.5693359375f);uint ah=(bits(affine)>>13)-0x1c000u;wf_ushort hb=static_cast<wf_ushort>(((ah<<5)+0x8000u)&65535u);ex[q*66+k]=__builtin_bit_cast(_Float16,hb);}
 }
 wf_sync();
 f8 sums[2];for(uint side=0;side<2;side++){f8 sum{};for(uint half=0;half<2;half++){h8 a{},ones{};for(uint e=0;e<8;e++){uint k=side*16+half*32+wf_gr()*8+e;a[e]=ex[(first+wf_rc())*66+k];ones[e]=(_Float16)1.f;}sum=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(a,ones,sum);}sums[side]=sum;}
 uint pv[8]{};
 #pragma unroll
 for(uint key=0;key<64;key+=16)for(uint e=0;e<8;e++){uint row=first+wf_gr()*8+e,k=key+wf_rc();float inv=1.f/(sums[0][e]+sums[1][e]);pv[e]|=wf_fp8(float(ex[row*66+k])*inv)<<(key/16*8);}
 wf_sync();
 unsigned char*prob=reinterpret_cast<unsigned char*>(ex);
 #pragma unroll
 for(uint key=0;key<64;key+=16)for(uint e=0;e<8;e++)prob[(first+wf_gr()*8+e)*68+key+wf_rc()]=static_cast<unsigned char>(pv[e]>>(key/16*8));
 wf_sync();
 f8 av[2]{};
 for(uint col=0;col<32;col+=16){f8 acc{};for(uint kt=0;kt<4;kt++){i2 a{},b{};
   for(uint e=0;e<8;e++){uint k=kt*16+wf_gr()*8+e;wf_put_bits(a,e,prob[(first+wf_rc())*68+k]);wf_put_bits(b,e,packed[k*36+col+wf_rc()]);}
   acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,acc);}av[col/16]=acc;}
 wf_sync();
 for(uint col=0;col<32;col+=16)for(uint e=0;e<8;e++)avbytes[(first+wf_gr()*8+e)*68+head*32+col+wf_rc()]=static_cast<unsigned char>(wf_fp8(F(av[col/16][e])));
 wf_sync();
 f8 result[2]{};
 {const unsigned char*diag=reinterpret_cast<const unsigned char*>(aw)+4*(4*64*64+2*4096+2+64);uint t=first+wf_rc();
  for(uint j=0;j<2;j++){uint ct=head*2+j;i2 a{};__builtin_memcpy(&a,feat+t*64+ct*16+wf_gr()*8,8);
   for(uint part=0;part<3;part++){i2 b{};__builtin_memcpy(&b,diag+(part*4+ct)*512+(wf_gr()*16+wf_rc())*8,8);result[j]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,result[j]);}}}
 for(uint k=0;k<64;k+=16){i2 a{};__builtin_memcpy(&a,avbytes+(first+wf_rc())*68+k+wf_gr()*8,8);for(uint j=0;j<2;j++){uint col=head*32+j*16+wf_rc(),off=3*64*64+(col*64+k+wf_gr()*8)/4;i2 b={int(aq[off]),int(aq[off+1])};result[j]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,result[j]);}}
 for(uint j=0;j<2;j++)for(uint e=0;e<8;e++){uint p=wf_raster(win,first+wf_gr()*8+e,workw),col=head*32+j*16+wf_rc(),dest=p*64+col;if(crop){uint x=p%workw,y=p/workw;if(x<sx||y<sy||x>=sx+width||y>=sy+height)continue;dest=((y-sy)*width+x-sx)*64+col;}float v=result[j][e],o=post==3?Hrtz(v):post==0?F(Hrtz(v)):F(v);if constexpr(ByteOut)out8[dest]=static_cast<unsigned char>(wf_fp8(o));else out[dest]=o;}
 }
#endif
}
#define C64_WINDOW_KERNEL(NAME,M,BI,BO) KERNEL __attribute__((amdgpu_flat_work_group_size(256,256))) void NAME(const float*in,const float*fw,const float*aw,void*out,uint width,uint height,uint workw,uint workh,uint sx,uint sy,uint post,uint crop){c64_window_body<M,BI,BO>(in,fw,aw,out,width,height,workw,workh,sx,sy,post,crop);}
C64_WINDOW_KERNEL(c64_window_fused,false,false,false)
C64_WINDOW_KERNEL(c64_window_fused_mapped,true,false,false)
C64_WINDOW_KERNEL(c64_window_fused_bytein,false,true,false)
C64_WINDOW_KERNEL(c64_window_fused_mapped_bytein,true,true,false)
C64_WINDOW_KERNEL(c64_window_fused_bout,false,false,true)
C64_WINDOW_KERNEL(c64_window_fused_mapped_bout,true,false,true)
C64_WINDOW_KERNEL(c64_window_fused_bytein_bout,false,true,true)
C64_WINDOW_KERNEL(c64_window_fused_mapped_bytein_bout,true,true,true)

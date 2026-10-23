// Append to c32_fused_ffn_attention.hip; use the MH component convention.
DEV uint mh_probe_code(uint code,uint k,uint pattern){if(pattern==1)return code^((k&1)*128);if(pattern==2){code=(code+k*37)&255;if((code&127)==127)code^=1;}return code;}
DEV float mh_probe_piece(float v){float m=absf(v);if(m<.015625f){float x=m*512.f;uint q=uint(x);float r=x-float(q);q+=uint(r>.5f||(r==.5f&&(q&1)));q=q>7?7:q;return (v<0?-1.f:1.f)*float(q)/512.f;}return F(v);}
// Append to c32_fused_ffn_attention.hip. Compare actual WMMA with ordered scalar FMAs.
KERNEL __attribute__((amdgpu_flat_work_group_size(32,32)))
void mh_diagonal_probe(const float*scales,uint*out,uint count){
 uint g=bid(),index=g/(256*3),code=(g/3)%256,pattern=g%3,l=__builtin_amdgcn_workitem_id_x();if(index>=count)return;
 if((code&127)==127){if(!l){out[g*3]=0;out[g*3+1]=0;out[g*3+2]=0;}return;}
 f8 acc[2]{};float scalar[2]{};
 for(uint part=0;part<3;part++){float remaining=scales[index],piece=0;for(uint j=0;j<=part;j++){piece=mh_probe_piece(remaining);remaining-=piece;}
  for(uint ci=0;ci<2;ci++)for(uint kt=0;kt<2;kt++){i2 a{},b{};for(uint e=0;e<8;e++){uint k=kt*16+gr()*8+e;put_bits(a,e,mh_probe_code(code,k,pattern));put_bits(b,e,k==ci*16+rc()?fp8(piece):0u);}acc[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,acc[ci]);float x=__builtin_amdgcn_cvt_f32_fp8(int(mh_probe_code(code,ci*16+rc(),pattern)),0);scalar[ci]=__builtin_fmaf(x,kt==ci?piece:0.f,scalar[ci]);}
 }
 bool bad=false;for(uint ci=0;ci<2;ci++)for(uint e=0;e<8;e++)bad|=bits(acc[ci][e])!=bits(scalar[ci]);
 uint mask=__builtin_amdgcn_ballot_w32(bad);if(!l){out[g*3]=mask;out[g*3+1]=bits(acc[0][0]);out[g*3+2]=bits(scalar[0]);}
}

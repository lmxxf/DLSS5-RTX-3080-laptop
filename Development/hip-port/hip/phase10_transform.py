"""Phase 10: exact per-entry register ceilings, emitted before the O4 driver JIT."""
import re
REGISTER_CAPS={
 'c64_wave2_bi_bo_w16':168,'c64_wave2_bi_w16':168,'c64_wave2_bi_ho':168,'c64_wave2_up_lb_sh':168,
 'c128_wave2_bi_bo_w16':168,'c128_wave2_bi_ho':168,'c128_wave2_up_lb_sh':168,
 'c512_qkv_attention_compact_w16':128,'c32_wave1_up_b8_w16':168}

def apply_register_caps(ptx):
 changes=[]
 for m in re.finditer(r'\.visible\s+\.entry\s+(\w+)\s*\(',ptx):
  if m[1] not in REGISTER_CAPS:continue
  a=ptx.index('{',m.end());header=ptx[m.start():a]
  if '.maxnreg' in header:continue
  changes.append((a,f'.maxnreg {REGISTER_CAPS[m[1]]}\n'))
 for a,new in reversed(changes):ptx=ptx[:a]+new+ptx[a:]
 return ptx

# Finite inputs: identical to old outer-clamp + E4M3 conversion. Preserve each
# caller's existing +0 convention; cw_z currently intentionally preserves -0.
def optimize_fp8(text):
 from phase2_transform import masked,end_at,args_of
 mask=masked(text);changes=[]
 for name in ('sm86_f32_to_e4m3_byte','sm86_c32_lowreg_byte'):
  m=re.search(r'\b'+name+r'\s*\(float x\)',mask)
  if not m:continue
  a=mask.index('{',m.end());z=end_at(mask,a,'{','}');old=text[a:z+1]
  if '.reg .pred p_sub' in old:
   body=r'''{
    sm86_u32 res;
    asm("{\n\t"
        " .reg .b32 b, a, r, sub, norm, mag, s;\n\t"
        " .reg .f32 fmagic;\n\t"
        " .reg .pred p_sub;\n\t"
        " mov.b32 b, %1;\n\t"
        " and.b32 a, b, 0x7fffffff;\n\t"
        " shr.u32 s, b, 24;\n\t"
        " and.b32 s, s, 0x80;\n\t"
        " min.f32 a, a, 0f43e00000;\n\t"
        " add.rn.f32 fmagic, a, 0f46800000;\n\t"
        " mov.b32 sub, fmagic;\n\t"
        " and.b32 sub, sub, 0xff;\n\t"
        " bfe.u32 r, a, 20, 1;\n\t"
        " add.u32 r, a, r;\n\t"
        " add.u32 r, r, 0x7ffff;\n\t"
        " shr.u32 norm, r, 20;\n\t"
        " add.s32 norm, norm, -960;\n\t"
        " setp.lt.u32 p_sub, a, 0x3c800000;\n\t"
        " selp.b32 mag, sub, norm, p_sub;\n\t"
        " or.b32 %0, s, mag;\n\t"
        "}" : "=r"(res) : "f"(x));
    return res;
}'''
  else:
   # Keep the short-live-range C++ shape selected for sensitive Phase-9 kernels.
   body=r'''{
    sm86_u32 b=__builtin_bit_cast(sm86_u32,x),s=(b>>24)&128,a=b&0x7fffffff;
    float fa;
    asm("min.f32 %0,%1,0f43e00000;":"=f"(fa):"f"(__builtin_bit_cast(float,a)));
    a=__builtin_bit_cast(sm86_u32,fa);
    if(a<0x3c800000u){
        float magic;
        asm volatile("add.rn.f32 %0,%1,0f46800000;":"=f"(magic):"f"(fa));
        return s|(__builtin_bit_cast(sm86_u32,magic)&255u);
    }
    sm86_u32 norm;
    asm volatile("{ .reg .b32 r, lsb; bfe.u32 lsb,%1,20,1; add.u32 r,%1,lsb; add.u32 r,r,0x7ffff; shr.u32 r,r,20; add.s32 %0,r,-960; }"
                 : "=r"(norm) : "r"(a));
    return s|norm;
}'''
  changes.append((a,z+1,body))
 for a,z,b in reversed(changes):text=text[:a]+b+text[z:]
 # Only saturation in FP8 front-ends is redundant. Residual float clamps remain.
 mask=masked(text);changes=[]
 for m in re.finditer(r'\b(?:float|unsigned char|uint)\s+(cw_z|w2_z|fp8_add0|F|fp8|byte_F|cw_up_F)\s*\(float (\w+)\)',mask):
  a=end_at(mask,mask.index('(',m.start()))+1
  while a<len(mask) and mask[a].isspace():a+=1
  if a>=len(mask) or mask[a]!='{':continue
  z=end_at(mask,a,'{','}');b=text[a:z+1];bm=masked(b);ed=[]
  for c in re.finditer(r'\b__builtin_amdgcn_fmed3f\s*\(',bm):
   end=end_at(bm,c.end()-1);args=args_of(b[c.end():end])
   if len(args)==3 and args[1] in ('-448.f','-448.0f') and args[2] in ('448.f','448.0f'):ed.append((c.start(),end+1,'('+args[0]+')'))
  for i,j,new in reversed(ed):b=b[:i]+new+b[j:]
  if ed:changes.append((a,z+1,b))
 for a,z,b in reversed(changes):text=text[:a]+b+text[z:]
 return text

"""Pack C32 FFN features directly from their already-rounded half storage.

At this one producer site the original RTZ residual write is retained. The
packed-half encoder has an exhaustive finite-half primitive test. Other FP8
sites (float activations, normalization, coordinate-dependent values) stay put.
"""
HALF_PACK_HELPER=r'''
__attribute__((device,always_inline)) inline sm86_u32 sm86_pack_half_pair_e4m3(sm86_u32 h){
 sm86_u32 out;
 asm("{ .reg .b32 a, sub, r, lsb, norm, lo, hi, s, clamp, magic; .reg .pred p0,p1;\n\t"
     "and.b32 a,%1,0x7fff7fff;\n\t"
     "mov.b32 clamp,0x5f005f00; min.f16x2 a,a,clamp;\n\t"
     "mov.b32 magic,0x40004000; add.rn.f16x2 sub,a,magic;\n\t"
     "shr.u32 lsb,a,7; and.b32 lsb,lsb,0x00010001;\n\t"
     "add.u32 r,a,0x003f003f; add.u32 r,r,lsb;\n\t"
     "shr.u32 norm,r,7; add.u32 norm,norm,0x00c000c0;\n\t"
     "and.b32 norm,norm,0x00ff00ff;\n\t"
     "and.b32 lo,a,0xffff; shr.u32 hi,a,16;\n\t"
     "setp.lt.u32 p0,lo,0x2400; setp.lt.u32 p1,hi,0x2400;\n\t"
     "selp.b32 lo,sub,norm,p0; selp.b32 hi,sub,norm,p1;\n\t"
     "and.b32 lo,lo,0xff; and.b32 hi,hi,0x00ff0000; or.b32 r,lo,hi;\n\t"
     "shr.u32 s,%1,8; and.b32 s,s,0x00800080; or.b32 r,r,s;\n\t"
     "prmt.b32 %0,r,0,0x4420; }" : "=r"(out):"r"(h));
 return out;
}
__attribute__((device,always_inline)) inline sm86_i2 sm86_pack_half_h8_e4m3(sm86_h8 h){
 sm86_u4 a=__builtin_bit_cast(sm86_u4,h);
 sm86_u32 p0=sm86_pack_half_pair_e4m3(a[0]),p1=sm86_pack_half_pair_e4m3(a[1]);
 sm86_u32 p2=sm86_pack_half_pair_e4m3(a[2]),p3=sm86_pack_half_pair_e4m3(a[3]);
 return sm86_i2{(int)(p0|(p1<<16)),(int)(p2|(p3<<16))};
}
'''

def pack_ffn_half_features(text):
    import re
    at=text.index('using cw_h2=')
    text=text[:at]+HALF_PACK_HELPER+text[at:]
    pat=r'i2 a;float a_t\[8\];\s*h8 rounded=cw_rtz_half8\(ffn\[ci\]\);(__builtin_memcpy\(residual[^;]+;).*?a=cw_pack8<2,cw_kind,\(!Up&&cw_kind==1\)>\(a_t\);'
    text,n=re.subn(pat,lambda m:'h8 rounded=cw_rtz_half8(ffn[ci]);'+m[1]+'i2 a=sm86_pack_half_h8_e4m3(rounded);',text,count=1,flags=re.S)
    assert n==1,n
    return text

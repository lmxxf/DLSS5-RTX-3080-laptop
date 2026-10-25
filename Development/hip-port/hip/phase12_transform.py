"""Phase12 selected C32 AV half producer; Q/K and float activations excluded."""
from phase11_transform import HALF_PACK_HELPER
ADAPTER=r'''
template<bool AddZero> __attribute__((device,always_inline)) inline sm86_i2 sm86_pack_ad_producer(sm86_u4 d){
 sm86_u32 k=AddZero?0u:0x3c003c00u;
 _Pragma("unroll") for(unsigned i=0;i<4;i++){
  if constexpr(AddZero)asm("add.rn.f16x2 %0,%1,%2;":"=r"(d[i]):"r"(d[i]),"r"(k));
  else asm("mul.rn.f16x2 %0,%1,%2;":"=r"(d[i]):"r"(d[i]),"r"(k));
 }
 return sm86_pack_half_h8_e4m3(__builtin_bit_cast(sm86_h8,d));
}
'''

def pack_c32_av(text):
    """C32 AV only: preserve signed zero and canonicalize NaNs before byte packing."""
    import re
    assert HALF_PACK_HELPER in text, "Phase11 helper must be applied first"
    at=text.index(HALF_PACK_HELPER)+len(HALF_PACK_HELPER)
    text=text[:at]+ADAPTER+text[at:]
    pattern=r'acc=sm86_unpack_acc\(__sm86_c_to_ampere\(acc\)\);i2 a;float a_t\[8\];.*?a=cw_pack8<5,cw_kind,\(!Up&&cw_kind==1\)>\(a_t\);av\[ci\]=sm86_d_bytes_to_ab\(a\);'
    text,n=re.subn(pattern,'i2 a=sm86_pack_ad_producer<false>(__sm86_c_to_ampere(acc));av[ci]=sm86_d_bytes_to_ab(a);',text,count=1,flags=re.S)
    assert n==1, ('C32 AV structural match changed',n)
    return text

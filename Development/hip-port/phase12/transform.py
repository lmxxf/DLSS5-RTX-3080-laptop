"""Four separately audited sites. Q/K and float activations are excluded."""
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

def inject(text):
 if 'sm86_pack_ad_producer' in text:return text
 if HALF_PACK_HELPER in text:
  a=text.index(HALF_PACK_HELPER)+len(HALF_PACK_HELPER);return text[:a]+ADAPTER+text[a:]
 a=text.index('using f8=');return text[:a]+HALF_PACK_HELPER+ADAPTER+text[a:]

def transform(text,site):
 import re
 text=inject(text)
 if site=='c32-av':
  pat=r'acc=sm86_unpack_acc\(__sm86_c_to_ampere\(acc\)\);i2 a;float a_t\[8\];.*?a=cw_pack8<5,cw_kind,\(!Up&&cw_kind==1\)>\(a_t\);av\[ci\]=sm86_d_bytes_to_ab\(a\);'
  new='i2 a=sm86_pack_ad_producer<false>(__sm86_c_to_ampere(acc));av[ci]=sm86_d_bytes_to_ab(a);'
  text,n=re.subn(pat,new,text,count=1,flags=re.S);assert n==1,n
 elif site=='wave2-av':
  pat=r'av=sm86_unpack_acc\(__sm86_c_to_ampere\(av\)\);i2 a;float a_t\[8\];.*?a=w2_pack8\(a_t\);w2_store<C>\(plane1,qt,head\*2\+ci,sm86_d_bytes_to_ab\(a\)\);'
  new='i2 a=sm86_pack_ad_producer<true>(__sm86_c_to_ampere(av));w2_store<C>(plane1,qt,head*2+ci,sm86_d_bytes_to_ab(a));'
  text,n=re.subn(pat,new,text,count=1,flags=re.S);assert n==1,n
 elif site in ['c32-v','wave2-v']:
  # Keep Q/K's exact existing scalar normalization and packing in the else arm.
  if site=='c32-v':
   pat=r'if\(part==2\)\{q\[ci\]=sm86_unpack_acc\(__sm86_c_to_ampere\(q\[ci\]\)\);\}(i2 a;float a_t\[8\];.*?a=cw_pack8<3,cw_kind,\(!Up&&cw_kind==1\)>\(a_t\);)'
   def repl(m):
    old=m[1].replace('i2 a;','',1)
    return 'i2 a;if(part==2)a=sm86_pack_ad_producer<false>(__sm86_c_to_ampere(q[ci]));else{'+old+'}'
   text,n=re.subn(pat,repl,text,count=1,flags=re.S);assert n==1,n
  else:
   total=0
   for expr in ['q[part][ci]','q[ci]']:
    p=re.escape(expr)
    pat=r'if\(part==2\)\{'+p+r'=sm86_unpack_acc\(__sm86_c_to_ampere\('+p+r'\)\);\}(i2 a;float a_t\[8\];.*?a=w2_pack8\(a_t\);)'
    def repl(m,expr=expr):return 'i2 a;if(part==2)a=sm86_pack_ad_producer<true>(__sm86_c_to_ampere('+expr+'));else{'+m[1].replace('i2 a;','',1)+'}'
    text,n=re.subn(pat,repl,text,count=1,flags=re.S);assert n==1,(expr,n);total+=n
 return text

import re,struct
from phase2_transform import masked,end_at

def helper():
 def pair(x):v=struct.unpack('<H',struct.pack('<e',x))[0];return hex(v|(v<<16))
 return r'''
template<bool AddZero> __attribute__((device,always_inline)) inline sm86_i2 sm86_act20(sm86_u4 d){
 _Pragma("unroll") for(unsigned i=0;i<4;i++){
  sm86_u32 v=d[i],g,a,q,p;
  asm("max.f16x2 %0,%1,%2;":"=r"(g):"r"(v),"r"(NEG4));
  asm("min.f16x2 %0,%1,%2;":"=r"(g):"r"(g),"r"(POS4));
  a=g&0x7fff7fffu;
  asm("fma.rn.f16x2 %0,%1,%2,%3;":"=r"(q):"r"(a),"r"(C1),"r"(C2));
  asm("fma.rn.f16x2 %0,%1,%2,%3;":"=r"(p):"r"(g),"r"(q),"r"(C3));
  asm("mul.rn.f16x2 %0,%1,%2;":"=r"(d[i]):"r"(v),"r"(p));
 }
 return sm86_pack_ad_producer<AddZero>(d);
}
'''.replace('NEG4',pair(-4)+'u').replace('POS4',pair(4)+'u').replace('C1',pair(-.055908203125)+'u').replace('C2',pair(.447265625)+'u').replace('C3',pair(.89453125)+'u')

def transform(s,c32):
 name='cw_body' if c32 else 'swin_wave2_body';m=masked(s);at=m.index('void '+name+'(');a=m.index('{',end_at(m,m.index('(',at))+1);z=end_at(m,a,'{','}');body=s[a+1:z]
 pat=r'(expanded(?:\[[^\]]+\])*)=sm86_unpack_acc\(__sm86_c_to_ampere\(\1\)\);i2 (\w+);float \2_t\[8\];.*?\2=(?:cw_pack8<[^;]+>|w2_pack8)\(\2_t\);'
 body,n=re.subn(pat,lambda m:'i2 '+m[2]+'=sm86_act20<'+('false' if c32 else 'true')+'>(__sm86_c_to_ampere('+m[1]+'));',body,flags=re.S);assert n==(2 if c32 else 3),(name,n)
 s=s[:a+1]+body+s[z:];point=s.index('using cw_h2=') if c32 else s.index('using f8=');return s[:point]+helper()+s[point:]

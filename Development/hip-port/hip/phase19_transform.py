import re
from phase2_transform import masked,end_at,calls

def transform(s,mask):
 assert mask in [1,3]
 m=masked(s);at=m.index('void swin_wave2_body(');a=m.index('{',end_at(m,m.index('(',at))+1);z=end_at(m,a,'{','}');body=s[a+1:z]
 patterns=[('fw',0),('fw+4*C*C',1),('fw+8*C*C',2)]
 for ptr,region in patterns:
  pat=r'w2_i4 w=w2_weight16\('+re.escape(ptr)+r',([^;]+)\);i2 b0=\{w\[0\],w\[1\]\},b1=\{w\[2\],w\[3\]\};'
  body,n=re.subn(pat,lambda m:'auto w=w19_weight16<C,'+str(region)+'>(fw,'+m[1]+');auto b0=w.lo,b1=w.hi;',body);assert n==1,(ptr,n)
 funcs=sorted(set(re.findall(r'sm86_wmma_fp8_maybe_pre_[ab]<[^>]+>',body)));count=[0]
 def change(fn,args,prior):
  if any(x in ['b0','b1'] for x in args[:2]):count[0]+=1;return 'w19_mma('+','.join(args)+')'
 body=calls(body,funcs,change);assert count[0]==6,count
 s=s[:a+1]+body+s[z:];m=masked(s);at=m.index('void swin_wave2_body(');template=s.rfind('template<',0,at);assert template>=0
 helper=r'''
struct w19_ref{const unsigned char*p;};
template<class T> struct w19_pair{T lo,hi;};
__attribute__((device,always_inline)) inline sm86_u4 w19_load(w19_ref w){sm86_u4 v;asm volatile("ld.global.nc.v4.u32 {%0,%1,%2,%3}, [%4];":"=r"(v[0]),"=r"(v[1]),"=r"(v[2]),"=r"(v[3]):"l"(w.p):"memory");return v;}
__attribute__((device,always_inline)) inline sm86_f8 w19_mma(w19_ref a,sm86_i2 b,sm86_f8 c){return __sm86_d_to_rdna4(sm86_mma_prepared_core(w19_load(a),__sm86_unpack_fp8(b),__sm86_c_to_ampere(c)));}
__attribute__((device,always_inline)) inline sm86_f8 w19_mma(sm86_i2 a,sm86_i2 b,sm86_f8 c){return sm86_wmma_fp8_preshuffled_ab(a,b,c);}
template<unsigned C,unsigned R> __attribute__((device,always_inline)) inline auto w19_weight16(const float*fw,unsigned row,unsigned stride,unsigned k,unsigned group=w2_gr()){
 if constexpr(C==64 || (C==128 && MASK19==3)){
  const unsigned off=((row/16)*(stride/32)+k/32)*512+(group*16+row%16)*16;
  const unsigned tail=(9*C*C+C)*4,region=R==0?0:R==1?8*C*C:16*C*C;
  const unsigned char*p=reinterpret_cast<const unsigned char*>(fw)+tail+region+2*off;
  return w19_pair<w19_ref>{{p},{p+16}};
 }else{w2_i4 w=w2_weight16(fw+(R==0?0:R==1?4*C*C:8*C*C),row,stride,k,group);return w19_pair<i2>{i2{w[0],w[1]},i2{w[2],w[3]}};}
}
'''.replace('MASK19',str(mask))
 return s[:template]+helper+s[template:]

def version_ptx(p,mask):return re.sub(r'(\.visible\s+\.entry\s+)(\w+)',lambda m:m[1]+f'w19m{mask}_'+m[2],p)

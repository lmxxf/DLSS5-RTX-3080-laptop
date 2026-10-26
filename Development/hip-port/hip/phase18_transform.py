"""Opt-in, site-local accumulator encoders. Never change Q/K or float activations."""
import re
from phase2_transform import masked,end_at
from phase11_transform import HALF_PACK_HELPER
from phase12_transform import ADAPTER

# Preserve the old D->RDNA4 permutation but keep half bits instead of expanding f32.
def helpers(s):
 if 'sm86_pack_ad_producer' not in s:
  at=s.index('using f8=');s=s[:at]+HALF_PACK_HELPER+ADAPTER+s[at:]
 if 'sm86_d_to_rdna4_half_bits' not in s:
  a=s.index('sm86_f8 __sm86_d_to_rdna4(sm86_u4 d)');a=s.index('{',a);z=end_at(s,a,'{','}');body=s[a:z+1]
  body=body.replace('return sm86_unpack_acc(sm86_u4{','return sm86_u4{').replace('p2 ? z1 : z3 });','p2 ? z1 : z3 };')
  assert 'sm86_unpack_acc' not in body
  at=s.index(HALF_PACK_HELPER)
  s=s[:at]+'__attribute__((device,always_inline)) inline sm86_u4 sm86_d_to_rdna4_half_bits(sm86_u4 d) '+body+'\n'+s[at:]
 return s

def transform(text,sites):
 text=helpers(text);name='cw_body' if any(x.startswith('c32-') for x in sites) else 'swin_wave2_body';m=masked(text);a=m.index('{',end_at(m,m.index('(',m.index('void '+name+'(')))+1);z=end_at(m,a,'{','}');b=text[a+1:z]
 for site in sites:
  if site in ['contract','result','av']:
   expr={'contract':r'contract(?:\[[^\]]+\])+','result':r'result\[ci\]','av':'av'}[site]
   pat=r'('+expr+r')=sm86_unpack_acc\(__sm86_c_to_ampere\(\1\)\);i2 a;float a_t\[8\];.*?a=w2_pack8\(a_t\);'
   b,n=re.subn(pat,lambda m:'i2 a=sm86_pack_ad_producer<true>(__sm86_c_to_ampere('+m[1]+'));',b,flags=re.S);assert n==({'contract':2,'result':1,'av':1}[site]),(site,n)
  elif site in ['v','c32-v']:
   exprs=['q[ci]'] if site=='c32-v' else ['q[part][ci]','q[ci]'];packer=r'cw_pack8<3,cw_kind,\(!Up&&cw_kind==1\)>' if site=='c32-v' else 'w2_pack8'
   for expr in exprs:
    pat=r'if\(part==2\)\{'+re.escape(expr)+r'=sm86_unpack_acc\(__sm86_c_to_ampere\('+re.escape(expr)+r'\)\);\}(i2 a;float a_t\[8\];.*?a='+packer+r'\(a_t\);)'
    b,n=re.subn(pat,lambda m:'i2 a;if(part==2)a=sm86_pack_ad_producer<'+('false' if site=='c32-v' else 'true')+'>(__sm86_c_to_ampere('+expr+'));else{'+m[1].replace('i2 a;','',1)+'}',b,count=1,flags=re.S);assert n==1,(site,expr,n)
  elif site=='byteout':
   pat=r'if constexpr\(ByteOut\)\{i2 a;float a_t\[8\];.*?a=w2_pack8\(a_t\);'
   found=list(re.finditer(pat,b,re.S));assert len(found)==1,(site,len(found))
   at=max(b.rfind('if(full||',0,found[0].start()),b.rfind('if(x>=sx',0,found[0].start()));assert at>=0 and found[0].start()-at<600
   capture='i2 w2_half_byteout[2];if constexpr(ByteOut){_Pragma("unroll") for(uint ci=0;ci<2;ci++)w2_half_byteout[ci]=sm86_pack_ad_producer<true>(sm86_d_to_rdna4_half_bits(__sm86_c_to_ampere(result[ci])));}'
   b=b[:at]+capture+b[at:]
   b,n=re.subn(pat,'if constexpr(ByteOut){i2 a=w2_half_byteout[ci];',b,flags=re.S);assert n==1,(site,n)
  elif site=='c32-prefix':
   pat=r'i2 packed;float packed_t\[8\];(.*?)packed=cw_pack8<0,cw_kind,\(!Up&&cw_kind==1\)>\(packed_t\);input\[ci\]=packed;'
   def repl(m):
    old=m[1];old,n=re.subn(r'packed_t\[e\]=\(v\);','',old);assert n==1,n
    return old+'input[ci]=sm86_d_bytes_to_ab(sm86_pack_ad_producer<false>(__sm86_c_to_ampere(pre)));'
   b,n=re.subn(pat,repl,b,count=1,flags=re.S);assert n==1,(site,n)
   old='input[0]=sm86_preshuffle_fp8(input[0]);input[1]=sm86_preshuffle_fp8(input[1]);';assert b.count(old)==2;at=b.rfind(old);b=b[:at]+'if constexpr(!Prefix){'+old+'}'+b[at+len(old):]
  else:raise ValueError(site)
 return text[:a+1]+b+text[z:]


def apply_c256_cap(ptx,cap):
 assert 1<=cap<=255
 edits=[]
 for m in re.finditer(r'\.visible\s+\.entry\s+(\w+)\s*\(',ptx):
  if m[1] not in ['c256_wave2_bi_bo_w16','c256_wave2_bi_w16']:continue
  a=ptx.index('{',m.end());header=ptx[m.start():a]
  if re.search(r'\.maxnreg\s+\d+',header):new=re.sub(r'\.maxnreg\s+\d+','.maxnreg '+str(cap),header)
  else:new=header+'.maxnreg '+str(cap)+'\n'
  edits.append((m.start(),a,new))
 assert len(edits)==2,len(edits)
 for a,z,new in reversed(edits):ptx=ptx[:a]+new+ptx[z:]
 return ptx

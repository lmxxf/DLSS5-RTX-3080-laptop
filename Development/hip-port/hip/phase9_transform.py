"""Value fragments are elementwise: normalize Q/K unchanged, bridge only V."""
import re
from phase2_transform import masked,end_at
from phase8_transform import amp

def transform(text):
 mask=masked(text);changes=[]
 for name in ['cw_body','swin_wave2_body']:
  m=re.search(r'\bvoid\s+'+name+r'\s*\(',mask)
  if not m:continue
  i=end_at(mask,m.end()-1)+1
  while mask[i].isspace():i+=1
  j=end_at(mask,i,'{','}');b=text[i+1:j];edits=[]
  pack='cw_pack8' if name=='cw_body' else 'w2_pack8'
  pat=re.compile(r'\bi2 a;float a_t\[8\];(.*?)a='+pack+r'(?:<[^;]+?>)?\(a_t\);',re.S)
  for q in pat.finditer(b):
   reads=re.findall(r'\b(q(?:\[[^\]]+\])+)\[e\]',q[1])
   if not reads:continue
   expr=reads[0]
   if expr not in ('q[ci]','q[part][ci]'):continue
   tail=b[q.end():q.end()+160];sh='sm86_preshuffle_fp8(a)';p=tail.find(sh)
   if p<0:continue
   # This site stores qkv_cached (C32), or writes Q/K to shared and V to vals.
   if name=='cw_body':assert 'qkv_cached=' in tail[:p] or 'cw_qkv_smem[' in tail[:p]
   else:assert 'if(part==0)' in tail
   edits.append((q.start(),q.start(),'if(part==2){'+amp(expr)+'}'))
   pos=q.end()+p;edits.append((pos,pos+len(sh),'(part==2?sm86_d_bytes_to_ab(a):sm86_preshuffle_fp8(a))'))
  assert len(edits)==(2 if name=='cw_body' else 4),(name,len(edits))
  for a,z,new in reversed(edits):b=b[:a]+new+b[z:]
  changes.append((i+1,j,b))
 for a,z,b in reversed(changes):text=text[:a]+b+text[z:]
 return text

def c32_mapped_lowreg(text):
    """Keep prefix/Up branchless; use the low-live-range encoder only for mapped."""
    from phase8_transform import low_register_fp8
    old=low_register_fp8(text);om=masked(old);m=re.search(r'\bsm86_f32_to_e4m3_byte\s*\(float x\)',om);a=om.index('{',m.end());z=end_at(om,a,'{','}')
    helper='__attribute__((device,always_inline)) inline sm86_u32 sm86_c32_lowreg_byte(float x)'+old[a:z+1]+'\n'
    helper+='''template<bool Lowreg> __attribute__((device,always_inline)) inline int sm86_c32_policy_pack(float a,float b,int old,bool word_sel){
 if constexpr(!Lowreg)return __builtin_amdgcn_cvt_pk_fp8_f32(a,b,old,word_sel);
 else{sm86_u32 lo=sm86_c32_lowreg_byte(a),hi=sm86_c32_lowreg_byte(b),pair=lo|(hi<<8),uold=(sm86_u32)old;
 return (int)(word_sel?((uold&0xffffu)|(pair<<16)):((uold&0xffff0000u)|pair));}}
'''
    mask=masked(text);m=re.search(r'\bcw_pack8\s*\(const float\*t\)',mask);assert m
    start=mask.index('{',m.end());stop=end_at(mask,start,'{','}')
    body=text[start:stop+1];assert body.count('__builtin_amdgcn_cvt_pk_fp8_f32')==4
    body=body.replace('__builtin_amdgcn_cvt_pk_fp8_f32','sm86_c32_policy_pack<Lowreg>')
    text=text[:start]+body+text[stop+1:]
    pat=r'template<uint Site,uint Kind>(?=\s+__attribute__[^\n]*\bcw_pack8\()'
    text,n=re.subn(pat,lambda _:helper+'template<uint Site,uint Kind,bool Lowreg=false>',text);assert n==1,n
    mask=masked(text);m=re.search(r'\bvoid\s+cw_body\s*\(',mask);a=end_at(mask,m.end()-1)+1
    while mask[a].isspace():a+=1
    z=end_at(mask,a,'{','}');body=text[a:z+1]
    body,n=re.subn(r'cw_pack8<([^,<>]+),cw_kind>',r'cw_pack8<\1,cw_kind,(!Up&&cw_kind==1)>',body);assert n>5,n
    return text[:a]+body+text[z+1:]

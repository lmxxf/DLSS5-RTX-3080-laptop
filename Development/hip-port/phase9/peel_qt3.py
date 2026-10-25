"""Consume Q3 once before qt=0..2, so q_reg3 is dead over the main loop."""
import re
from phase2_transform import masked,end_at

def transform(text):
 mask=masked(text);m=re.search(r'\bvoid\s+cw_body\s*\(',mask);assert m
 start=end_at(mask,m.end()-1)+1
 while mask[start].isspace():start+=1
 stop=end_at(mask,start,'{','}');b=text[start+1:stop];bm=masked(b)
 loops=list(re.finditer(r'for\(uint qt=0;qt<4;qt\+\+\)',bm));assert len(loops)==2,len(loops)
 m=loops[1];a=bm.index('{',m.end());z=end_at(bm,a,'{','}');body=b[a+1:z]
 assert 'q_reg3' in body
 # For the remaining loop qt is provably 0,1,2; remove the impossible fallback.
 rest=body
 for ci in (0,1):
  old=f'qt==0?q_reg0[{ci}]:qt==1?q_reg1[{ci}]:qt==2?q_reg2[{ci}]:q_reg3[{ci}]'
  assert old in rest
  rest=rest.replace(old,f'qt==0?q_reg0[{ci}]:qt==1?q_reg1[{ci}]:q_reg2[{ci}]')
 assert 'q_reg3' not in rest
 pragma=b.rfind('#pragma clang loop unroll(disable)',0,m.start());assert pragma>=0
 assert b[pragma:m.start()].strip()=='#pragma clang loop unroll(disable)'
 replacement='{ const uint qt=3;'+body+'}\n#pragma clang loop unroll(disable)\nfor(uint qt=0;qt<3;qt++){'+rest+'}'
 b=b[:pragma]+replacement+b[z+1:]
 return text[:start+1]+b+text[stop:]

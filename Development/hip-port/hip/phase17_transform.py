"""V3 C32-only appended FP16 static fragments; applied after existing semantic passes."""
import re
from phase2_transform import calls,masked,end_at

def transform(s):
 m=masked(s);a=m.index('{',m.index('void cw_body('));z=end_at(m,a,'{','}');body=s[a+1:z]
 rules=[
 ('cw_i2_pair bp=cw_matrix16(fw,34944+part*512+(g*16+r)*16);','cw_half_pair bp=cw_half_matrix16(fw,57472,part*512+(g*16+r)*16);'),
 ('cw_i2_pair bp=cw_matrix16(fw+512,ht*512+(g*16+r)*16);','cw_half_pair bp=cw_half_matrix16(fw+512,39040,ht*512+(g*16+r)*16);'),
 ('cw_i2_pair cp=cw_matrix16(fw+4608,(ci*4+h2)*512+(g*16+r)*16);','cw_half_pair cp=cw_half_matrix16(fw+4608,30848,(ci*4+h2)*512+(g*16+r)*16);'),
 ('cw_i2_pair bp=cw_matrix16(w,(part*2+ci)*512+(qg*16+qr)*16);','cw_half_pair bp=cw_half_matrix16(w,32912,(part*2+ci)*512+(qg*16+qr)*16);'),
 ('cw_i2_pair bp=cw_matrix16(w,3072+ci*512+(g*16+r)*16);','cw_half_pair bp=cw_half_matrix16(w,32912,3072+ci*512+(g*16+r)*16);')]
 for old,new in rules:
  assert old in body,old;body=body.replace(old,new)
 count=[0,0]
 def change(fn,args,prior):
  if len(args)!=3:return
  for i in [0,1]:
   if args[i] in ['bp.lo','bp.hi','cp.lo','cp.hi']:
    count[i]+=1;return 'sm86_c32_half_'+('a' if i==0 else 'b')+'('+','.join(args)+')'
 # Template arguments are part of the callee spelling after Phase2.
 funcs=sorted(set(re.findall(r'sm86_wmma_fp8_maybe_pre_[ab]<[^>]+>',body)))
 body=calls(body,funcs,change)
 assert count==[12,2],count
 assert not re.search(r'sm86_wmma_fp8_maybe_pre_[ab]<[^>]+>\((?:bp|cp)\.',body)
 return s[:a+1]+body+s[z:]

def version_ptx(ptx):
 # All exports get a distinct ABI namespace; old hosts cannot call them accidentally.
 return re.sub(r'(\.visible\s+\.entry\s+)(\w+)',lambda m:m[1]+'v3_'+m[2],ptx)

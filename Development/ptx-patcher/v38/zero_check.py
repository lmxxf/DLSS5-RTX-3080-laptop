"""Independent bit-level zero witness: only mov/cvt of proven +0, no interval arithmetic."""
from analysis_common import Origin,REG,split_args
import bisect,re,json,collections

def witnesses(text):
 o=Origin(text);cache={};busy=set()
 def value(r,point):
  try:return int(r,0)==0
  except ValueError:pass
  key=(r,point)
  if key in cache:return cache[key]
  if key in busy:return False
  busy.add(key);ds=o.reach(r,point);good=bool(ds)
  for j,reg in ds:
   if j<0:good=False;continue
   x=o.ins[j];a=x['argv'];op=x['op']
   if op.startswith('mov.'):
    args=split_args(a[1].strip('{}')) if a[1].startswith('{') else [a[1]];ok=all(value(v.strip(),j) for v in args)
   elif op=='cvt.rn.f16.f32':ok=value(a[1],j)
   else:ok=False
   good=good and ok
  busy.remove(key);cache[key]=good;return good
 return o,value

def check(text,rows):
 o,proof=witnesses(text)
 for r in rows:
  if r['kind']=='pack3' and r['range']==[0.,0.]:
   # Source location includes only this entry; find the original conversion.
   matches=[(j,x) for j,x in enumerate(o.ins) if x['op']=='cvt.rn.satfinite.e4m3x2.f16x2' and x['argv']==[r['destination'],r['source']]]
   assert len(matches)==1,(r,matches)
   assert proof(r['source'],matches[0][0]),r

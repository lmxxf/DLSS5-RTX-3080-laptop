"""Conservative CFG interval/sign analysis; unknown and -0 never qualify for pack3."""
import re,struct,math,json,collections,bisect
from analysis_common import Origin,entries,b,REG,split_args
AUDIT=[]
UNKNOWN=(-math.inf,math.inf,True,False)
def h(bits):
 return struct.unpack('<e',struct.pack('<H',bits&65535))[0]
def scalar(bits,width):return struct.unpack('<f',struct.pack('<I',bits&0xffffffff))[0] if width==32 else h(bits)
def const(value,width):
 try:
  if value.startswith('0f'):
   n=int(value[2:],16);values=[h(n),h(n>>16)] if width==32 else [h(n)]
  elif value.startswith('0x'):n=int(value,16);values=[h(n),h(n>>16)] if width==32 else [h(n)]
  else:
   n=int(value,0);values=[h(n),h(n>>16)] if width==32 else [h(n)]
 except (ValueError,OverflowError):return UNKNOWN
 finite=[v for v in values if not math.isnan(v)]
 return (min(finite,default=-math.inf),max(finite,default=math.inf),len(finite)!=len(values),all(v>=0 and (v!=0 or math.copysign(1,v)>0) for v in finite) and len(finite)==len(values))
class Range:
 def __init__(self,text):
  self.o=Origin(text);self.cache={};self.busy=set();self.witness={};self.bf=list(re.finditer(r'[{}]',text));self.bp=[m.start() for m in self.bf];self.paths=[()];stack=[]
  for i,m in enumerate(self.bf):
   if m[0]=='{':stack.append(i)
   elif stack:stack.pop()
   self.paths.append(tuple(stack))
 def value(self,r,point,half=False):
  if not REG.fullmatch(r):
   z=const(r,16 if half else 32)
   if z!=UNKNOWN:return z
   return self.named_half(r,point) if half else UNKNOWN
  key=(r,point,half)
  if key in self.cache:return self.cache[key]
  if key in self.busy:return UNKNOWN
  self.busy.add(key);ds=self.o.reach(r,point);vals=[]
  for j,s in ds:vals.append(self.ins(j,s,half) if j>=0 else UNKNOWN)
  self.busy.remove(key);v=(min(x[0] for x in vals),max(x[1] for x in vals),any(x[2] for x in vals),all(x[3] for x in vals)) if vals else UNKNOWN;self.cache[key]=v;return v
 def ins(self,j,dest,half):
  x=self.o.ins[j];op=x['op'];a=x['argv']
  if op.startswith('mov.'):
   if len(a)<2:return UNKNOWN
   if a[1].startswith('{'):
    rr=split_args(a[1].strip('{}'));vs=[self.value(r.strip(),j,True) for r in rr]
    return (min(x[0] for x in vs),max(x[1] for x in vs),any(x[2] for x in vs),all(x[3] for x in vs)) if vs else UNKNOWN
   return self.value(a[1],j,half)
  if half and op.startswith('cvt.') and '.f16.f32' in op:
   z=self.f32(a[1],j)
   if z[2] or z[0]<-448 or z[1]>448:return UNKNOWN
   return z
  if op.startswith('abs.f16x2'):
   z=self.value(a[1],j);return (0,max(abs(z[0]),abs(z[1])),z[2],True)
  if op.startswith(('min.f16x2','max.f16x2')):
   x1=self.value(a[1],j);x2=self.value(a[2],j)
   if op.startswith('min'):lo,hi=min(x1[0],x2[0]),min(x1[1],x2[1])
   else:lo,hi=max(x1[0],x2[0]),max(x1[1],x2[1])
   # minNum/maxNum return non-NaN operand; .NaN propagation is not assumed safe.
   nan=(x1[2] and x2[2]) or ('.NaN' in op and (x1[2] or x2[2]))
   if x1[2]:lo=min(lo,x2[0]);hi=max(hi,x2[1])
   if x2[2]:lo=min(lo,x1[0]);hi=max(hi,x1[1])
   return lo,hi,nan,x1[3] and x2[3] and not nan
  if op.startswith('neg.f16x2'):
   z=self.value(a[1],j);return -z[1],-z[0],z[2],False
  return UNKNOWN

 def scope(self,j):return self.paths[bisect.bisect_right(self.bp,self.o.ins[j]['start'])]
 def named_half(self,r,point):
  bid=self.o.owner[point];scope=self.scope(point)
  for j in range(point-1,self.o.blocks[bid]['start']-1,-1):
   x=self.o.ins[j]
   if self.scope(j)==scope and x['argv'][0]==r:
    if x['guard']:return UNKNOWN
    return self.ins(j,r,True)
  return UNKNOWN
 def f32(self,r,point):
  if not REG.fullmatch(r):
   try:
    bits=int(r[2:],16) if r.startswith('0f') else int(r,0);v=scalar(bits,32)
    return (v,v,False,v>=0 and (v!=0 or math.copysign(1,v)>0)) if not math.isnan(v) else UNKNOWN
   except ValueError:return UNKNOWN
  key=('f32',r,point)
  if key in self.cache:return self.cache[key]
  if key in self.busy:return UNKNOWN
  self.busy.add(key);vs=[]
  for j,rr in self.o.reach(r,point):
   if j<0:vs.append(UNKNOWN);continue
   x=self.o.ins[j];op=x['op'];a=x['argv']
   if op.startswith('mov.'):z=self.f32(a[1],j)
   elif op.startswith('abs.f32'):
    q=self.f32(a[1],j);z=(0,max(abs(q[0]),abs(q[1])),q[2],True)
   elif op.startswith(('min.f32','max.f32')):
    q,t=self.f32(a[1],j),self.f32(a[2],j);fun=min if op.startswith('min') else max;lo,hi=fun(q[0],t[0]),fun(q[1],t[1])
    if q[2]:lo=min(lo,t[0]);hi=max(hi,t[1])
    if t[2]:lo=min(lo,q[0]);hi=max(hi,q[1])
    nan=q[2] and t[2];z=(lo,hi,nan,q[3] and t[3] and not nan)
   else:z=UNKNOWN
   vs.append(z)
  self.busy.remove(key);z=(min(x[0] for x in vs),max(x[1] for x in vs),any(x[2] for x in vs),all(x[3] for x in vs)) if vs else UNKNOWN;self.cache[key]=z;return z

def audit(text):
 records=[]
 for name,part in entries(text):
  rs=Range(part)
  for m in b.dp.FP8_DOWN_PATTERN.finditer(part):
   point=bisect.bisect_right(rs.o.starts,m.start())-1;z=rs.value(m['source'],point);kind='pack3' if not z[2] and z[3] and z[0]>=0 and z[1]<=448 else ('pack4' if not z[2] and z[0]>=-448 and z[1]<=448 else 'generic');defs=rs.o.reach(m['source'],point)
   records.append({'kernel':name,'line':part.count('\n',0,m.start())+1,'source':m['source'],'destination':m['destination'],'kind':kind,'range':[v if math.isfinite(v) else str(v) for v in z[:2]],'may_nan':z[2],'nonnegative_plus_zero_proved':z[3],'definitions':[{'index':j,'text':rs.o.ins[j]['text'] if j>=0 else 'undefined'} for j,r in sorted(defs)]})
 return records

def declarations():return ['.reg .b32 v36_a,v36_t;']
def pack(source,dest,kind='pack4'):
 lines=([f'abs.f16x2 v36_a,{source};'] if kind=='pack4' else [])+['mov.b32 v36_t,0x1c001c00;',f'mul.rn.f16x2 v36_a,{"v36_a" if kind=="pack4" else source},v36_t;','shl.b32 v36_a,v36_a,1;','add.u32 v36_a,v36_a,0x007f007f;']
 if kind=='pack4':lines += [f'lop3.b32 v36_a,{source},v36_a,0x7f007f00,0xd8;']
 return lines+['prmt.b32 v36_a,v36_a,0,0x4431;',f'cvt.u16.u32 {dest},v36_a;']

def lower(text,stats,stock,mode,fb):
 spec=json.loads((__import__('pathlib').Path(__file__).parent/'specs.json').read_text())[mode]
 rows=audit(text);AUDIT.extend(r|{'FB':fb} for r in rows);kinds={(r['kernel'],r['line'],r['source'],r['destination']):r for r in rows};parts=re.split(r'(?=\.visible \.entry )',text);count=0;zeros=0
 for i,part in enumerate(parts):
  if not part.startswith('.visible .entry '):continue
  name=re.match(r'\.visible \.entry (\w+)',part)[1]
  __import__('zero_check').check(part,[r for r in rows if r['kernel']==name])
  def replace(m):
   nonlocal count,zeros
   row=kinds[(name,part.count('\n',0,m.start())+1,m['source'],m['destination'])]
   if fb in spec.get('zero_fbs',[]) and name not in spec.get('zero_exclude_entries',[]) and row['kind']=='pack3' and row['range']==[0.,0.] and row['nonnegative_plus_zero_proved'] and not row['may_nan']:
    zeros+=1;count+=1;return f"mov.b16 {m['destination']},0;"
   if fb in spec.get('pack4',[]):
    count+=1;return '\n'.join(['{']+declarations()+pack(m['source'],m['destination'],'pack4')+['}'])
   return m[0]
  parts[i]=b.dp.FP8_DOWN_PATTERN.sub(replace,part)
 stats.add('fp16_to_fp8',count);stats.add('zero_constant_folds',zeros);return stock(''.join(parts),stats)

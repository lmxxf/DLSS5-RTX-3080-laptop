from pathlib import Path
import subprocess,json,re
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';prof=json.loads((p.parent/'v23/profile.json').read_text());active={r['name'] for r in prof['1280']['calls']};out={}
for mode in ['baseline','exact','fast']:
 rows={}
 for fb in range(7):
  f=p/f'artifacts/{mode}/fatbin{fb:02}.cubin';res=subprocess.check_output([tool,'-res-usage',str(f)],text=True);sass=subprocess.check_output([tool,'-sass',str(f)],text=True)
  for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
   if m[1] in active:rows[m[1]]={'FB':fb,**{k:int(v) for k,v in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}}
  for part in re.split(r'Function : ',sass)[1:]:
   n=part.splitlines()[0].strip()
   if n not in rows:continue
   ops=re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)',part);rows[n]['instructions']=len(ops)
   for op in ['HMMA','PRMT','LDL','STL','HADD2','HMUL2','HSET2']:rows[n][op]=sum(x.split('.')[0]==op for x in ops)
 out[mode]=rows
(p/'resources.json').write_text(json.dumps(out,indent=2)+'\n');print({m:{k:sum(r[k] for r in rows.values()) for k in ['instructions','HMMA','LDL','STL','PRMT']} for m,rows in out.items()})

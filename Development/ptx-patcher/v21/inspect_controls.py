from pathlib import Path
import subprocess,re,json,hashlib
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';dest=p/'resource-usage';dest.mkdir(exist_ok=True);rows={}
base=json.loads((p.parent/'v2/sass-resources.json').read_text())['new'];rows['baseline']=base
for f in sorted((p/'artifacts').glob('fb*-cap*/fatbin*.cubin')):
 key=f.parent.name;res=subprocess.run([tool,'-res-usage',str(f)],capture_output=True,text=True,check=True).stdout;sass=subprocess.run([tool,'-sass',str(f)],capture_output=True,text=True,check=True).stdout;(dest/(key+'.txt')).write_text(res);kernels={}
 for chunk in sass.split('Function : ')[1:]:
  name=chunk.splitlines()[0].strip();kernels[name]={k:len(re.findall(r'\b'+k+r'\b',chunk)) for k in ['SHFL','HMMA','LDL','STL']}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
  if m[1] in kernels:kernels[m[1]]['resources']={a:int(b) for a,b in re.findall(r'(REG|STACK|LOCAL|SHARED):(\d+)',m[2])}
 rows[key]={'kernels':kernels,'totals':{k:sum(r[k] for r in kernels.values()) for k in ['SHFL','HMMA','LDL','STL']},'max_stack':max(r.get('resources',{}).get('STACK',0) for r in kernels.values()),'sass_sha256':hashlib.sha256(sass.encode()).hexdigest(),'cubin_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 print(key,len(kernels),'max_stack',rows[key]['max_stack'],'LDL/STL',rows[key]['totals']['LDL'],rows[key]['totals']['STL'],flush=True)
(p/'resources.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# maxnreg controls: all exports, static counts','','| FB/cap | max STACK | LDL | STL | Max REG |','|---|---:|---:|---:|---:|']
for key,r in rows.items():
 if key=='baseline':
  for n,a in r.items():lines.append(f'| V2 {n} | {a["max_stack"]} | {a["totals"]["LDL"]} | {a["totals"]["STL"]} | {max(z.get("resources",{}).get("REG",0) for z in a["kernels"].values())} |')
 else:lines.append(f'| {key} | {r["max_stack"]} | {r["totals"]["LDL"]} | {r["totals"]["STL"]} | {max(z.get("resources",{}).get("REG",0) for z in r["kernels"].values())} |')
(p/'resources.md').write_text('\n'.join(lines)+'\n')

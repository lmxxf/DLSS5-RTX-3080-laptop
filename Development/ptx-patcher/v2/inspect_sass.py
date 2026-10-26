from pathlib import Path
import subprocess,re,json
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';rows={}
for tag in ['old','new','v7']:
 rows[tag]={};base=p/'artifacts'/tag
 files=sorted(base.glob('*.cubin'))
 if tag=='new':files=sorted(base.glob('fatbin*.cubin')) or sorted(base.glob('fb*-sm86.cubin'))
 if tag=='v7':files=[f for f in files if '-sm86.' in f.name]
 for f in files:
  i=int(re.search(r'(?:fb|fatbin)(\d+)',f.name)[1]);
  if i>6 and not(tag=='v7' and i>=15):continue
  rp=base/(f.stem+'-res.txt');res=rp.read_text() if rp.exists() else subprocess.run([tool,'-res-usage',str(f)],capture_output=True,text=True,check=True).stdout
  sp=base/(f.stem+'-sass.txt');sass=sp.read_text() if sp.exists() else subprocess.run([tool,'-sass',str(f)],capture_output=True,text=True,check=True).stdout
  (base/(f.stem+'-res.txt')).write_text(res);(base/(f.stem+'-sass.txt')).write_text(sass)
  kernels={}
  for chunk in sass.split('Function : ')[1:]:
   name=chunk.splitlines()[0].strip();kernels[name]={'SHFL':len(re.findall(r'\bSHFL\b',chunk)),'IMMA':len(re.findall(r'\bIMMA\b',chunk)),'HMMA':len(re.findall(r'\bHMMA\b',chunk)),'PRMT':len(re.findall(r'\bPRMT\b',chunk)),'LDL':len(re.findall(r'\bLDL\b',chunk)),'STL':len(re.findall(r'\bSTL\b',chunk))}
  for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
   name=m[1];ss=m[2]
   if name in kernels:kernels[name]['resources']={a:int(b) for a,b in re.findall(r'(REG|STACK|LOCAL|SHARED|CONSTANT\[\d+\]):(\d+)',ss)}
  rows[tag][f.stem]={'kernels':kernels,'totals':{k:sum(v[k] for v in kernels.values()) for k in ['SHFL','IMMA','HMMA','PRMT','LDL','STL']},'max_stack':max([v.get('resources',{}).get('STACK',0) for v in kernels.values()] or [0])}
assert all(len(rows[t])==7 for t in ['old','new','v7']), 'Extract/build modules first; require FB00..06 / V7 FB15..21'
(p/'sass-resources.json').write_text(json.dumps(rows,indent=2)+'\n')
for t,rr in rows.items():
 for f,a in rr.items():print(t,f,len(a['kernels']),a['totals'],'max_stack',a['max_stack'])

from pathlib import Path
import json,re,sys,numpy as np
p=Path(__file__).resolve().parent;r=p.parent

def check_variant(name,strict=True):
 rows={}
 for f in sorted(p.glob(name+'-*-run.json')):
  m=json.loads(f.read_text());w=m['width'];s=f.with_name(f.name.replace('-run.json','.log')).read_text();k={}
  for line in s.splitlines():
   a=line.split()
   if len(a)==10 and a[1].isdigit():k[a[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,a[1:])))
  out=np.fromfile(p/f'artifacts/outputs/{m["variant"]}-{w}.rgb32',np.uint32);ref=np.fromfile(r/f'phase17/artifacts/outputs/candidate-b-nc-abba-{w}.rgb32',np.uint32);diff=int(np.count_nonzero(out!=ref));val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);g=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s)
  rows[f.stem.replace('-run','')]={'variant':m['variant'],'width':w,'bitdiff':diff,'invalid':int(val[1]),'first_last':int(val[2]),'gpu_min':float(g[2]),'gpu_median':float(g[1]),'wall_median':float(wall[1]),'profile_total':float(re.search(r'PROFILE_TOTAL ([\d.]+)',s)[1]),'kernels':k,'LMem0':len(k)==32 and all(v['lmem']==0 for v in k.values())}
  if strict:assert diff==int(val[1])==int(val[2])==0 and rows[f.stem.replace('-run','')]['LMem0'],(f,rows[f.stem.replace('-run','')])
 return rows
if __name__=='__main__':
 name=sys.argv[1];rows=check_variant(name,False);(p/(name+'-quality.json')).write_text(json.dumps(rows,indent=2)+'\n');print(name,[(r['width'],r['bitdiff'],r['LMem0']) for r in rows.values()])

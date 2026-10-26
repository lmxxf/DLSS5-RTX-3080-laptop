from pathlib import Path
import json,re,subprocess
from check_run import check_variant
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';builds=json.loads((p/'control-builds.json').read_text());baseline=next(iter(check_variant('baseline-byteout-a',True).values()));active=[n for n in baseline['kernels'] if n.startswith(('c64_wave2','c128_wave2','c256_wave2'))];rows={}
for name,cfg in builds.items():
 mod=Path(cfg['modules'])/'c64-wave2-fast.hsaco';txt=subprocess.run([tool,'-res-usage',str(mod)],capture_output=True,text=True,check=True).stdout;(p/(name+'-resources.txt')).write_text(txt);res={}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',txt):res[m[1]]={a:int(b) for a,b in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}
 assert all(n in res for n in active),(name,active,res.keys());bad={n:res[n] for n in active if res[n]['STACK'] or res[n]['LOCAL']};row={'config':cfg,'active_wave2_resources':{n:res[n] for n in active},'spill_kernels':bad,'resource_gate':not bad}
 if bad:print('REJECT_RESOURCE',name,{n:r['STACK'] for n,r in bad.items()},flush=True)
 else:
  tag='control-quick-'+name;subprocess.run(['python3',str(p/'bench.py'),tag,'--modules',cfg['modules'],'--warmup','3','--iterations','5'],check=True);runs=check_variant(tag,True);assert len(runs)==3;row['quick']=runs;print('PASS_QUICK',name,flush=True)
 rows[name]=row;(p/'control-quick-results.json').write_text(json.dumps(rows,indent=2)+'\n')

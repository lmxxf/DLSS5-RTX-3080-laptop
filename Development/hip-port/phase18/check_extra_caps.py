from pathlib import Path
import json,subprocess,re
from check_run import check_variant
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';builds=json.loads((p/'control-builds.json').read_text());rows=json.loads((p/'control-quick-results.json').read_text());active=list(next(iter(rows.values()))['active_wave2_resources'])
for name in ['all-cap168','all-cap128','fuse7-cap128','pair15-cap128']:
 cfg=builds[name];text=subprocess.run([tool,'-res-usage',str(Path(cfg['modules'])/'c64-wave2-fast.hsaco')],capture_output=True,text=True,check=True).stdout;(p/(name+'-resources.txt')).write_text(text);res={}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',text):res[m[1]]={a:int(b) for a,b in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}
 bad={n:res[n] for n in active if res[n]['STACK'] or res[n]['LOCAL']};row={'config':cfg,'active_wave2_resources':{n:res[n] for n in active},'spill_kernels':bad,'resource_gate':not bad}
 if bad:print('REJECT_RESOURCE',name,{n:v['STACK'] for n,v in bad.items()},flush=True)
 else:
  tag='control-quick-'+name;subprocess.run(['python3',str(p/'bench.py'),tag,'--modules',cfg['modules'],'--warmup','3','--iterations','5'],check=True);row['quick']=check_variant(tag,True);assert len(row['quick'])==3;print('PASS_QUICK',name,flush=True)
 rows[name]=row;(p/'control-quick-results.json').write_text(json.dumps(rows,indent=2)+'\n')

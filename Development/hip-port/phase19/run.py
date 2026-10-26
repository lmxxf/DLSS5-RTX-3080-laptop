from pathlib import Path
import json,subprocess
from check_run import check_variant
p=Path(__file__).resolve().parent;rows=json.loads((p/'builds.json').read_text());quality={}
for mask,cfg in rows.items():
 tag='quick-m'+mask;subprocess.run(['python3',str(p/'bench.py'),tag,'--modules',cfg['modules'],'--warmup','3','--iterations','5'],check=True);rr=check_variant(tag,False)
 good=len(rr)==3 and all(x['bitdiff']==x['invalid']==x['first_last']==0 and x['LMem0'] for x in rr.values())
 for x in rr.values():
  for n,k in x['kernels'].items():
   if n.startswith(('c64_wave2','c128_wave2')):good=good and k['regs']<=168 and k['occw']>=12
 quality[mask]={'passed':bool(good),'quick':rr,'modules':cfg['modules']};print('PRECHECK',mask,good,flush=True)
(p/'precheck.json').write_text(json.dumps(quality,indent=2)+'\n')
f=(p/'abba-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f,stderr=subprocess.STDOUT)
try:
 for mask,cfg in quality.items():
  if not cfg['passed']:continue
  for w in [1280,1600,1920]:
   for part in ['baseline-a','candidate-b','candidate-b2','baseline-a2']:
    cmd=['python3',str(p/'bench.py'),part+'-m'+mask,'--width',str(w)]
    if not part.startswith('baseline'):cmd+=['--modules',cfg['modules']]
    subprocess.run(cmd,check=True)
finally:mon.terminate();mon.wait();f.close()

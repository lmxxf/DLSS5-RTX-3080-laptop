from pathlib import Path
import json,subprocess
p=Path(__file__).resolve().parent;quick=json.loads((p/'site-quick-results.json').read_text());f=(p/'sites-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f,stderr=subprocess.STDOUT)
try:
 for site in ['contract','result','v','av','byteout','c32-prefix','c32-v']:
  if not quick[site]['eligible_ABBA']:print('SKIP',site,'precheck',quick[site]['numeric'],quick[site]['LMem0'],flush=True);continue
  for w in [1280,1600,1920]:
   for name in ['baseline-'+site+'-a','site-'+site+'-b','site-'+site+'-b2','baseline-'+site+'-a2']:
    args=['python3',str(p/'bench.py'),name,'--width',str(w)]
    if not name.startswith('baseline'):args+=['--modules',quick[site]['modules']]
    subprocess.run(args,check=True)
  print('COMPLETE_SITE',site,flush=True)
finally:mon.terminate();mon.wait();f.close()

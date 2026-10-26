from pathlib import Path
import json,subprocess,argparse
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('--tag',default='final');a=a.parse_args();variant='fuse7';cfg=json.loads((p/'control-builds.json').read_text())[variant];
if not (p/'selection.json').exists():(p/'selection.json').write_text(json.dumps({'control':variant,'sites':{'c64-wave2-fast':['byteout'],'c32-wave1-fast':['c32-v']},'C256_cap':None,'QKV_mask':7,'reason':'C32 V and ByteOut positive across3tiers;Fuse7 strongest repeatable1080screen;128caps fail zero-spill;168no occupancy gain and no consistent added speed'},indent=2)+'\n')
if (p/'artifacts/selected/modules').is_dir():cfg['modules']=str(p/'artifacts/selected/modules')
f=(p/(a.tag+'-telemetry.csv')).open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f,stderr=subprocess.STDOUT)
try:
 for w in [1280,1600,1920]:
  for part in ['baseline-a','candidate-b','candidate-b2','baseline-a2']:
   cmd=['python3',str(p/'bench.py'),part+'-'+a.tag,'--width',str(w)]
   if not part.startswith('baseline'):cmd+=['--modules',cfg['modules']]
   subprocess.run(cmd,check=True)
finally:mon.terminate();mon.wait();f.close()

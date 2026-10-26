from pathlib import Path
import json,subprocess
p=Path(__file__).resolve().parent;rows=json.loads((p/'control-quick-results.json').read_text());cfg=json.loads((p/'control-builds.json').read_text());f=(p/'screen-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f,stderr=subprocess.STDOUT)
try:
 for name in ['pack-all','cap168','fuse7','pair15','fuse7-cap168','pair15-cap168','all-cap168','all-cap128','fuse7-cap128','pair15-cap128']:
  if not rows[name]['resource_gate']:print('SKIP_SPILL',name,flush=True);continue
  for suffix,variant in [('a','pack2'),('b',name),('b2',name),('a2','pack2')]:
   subprocess.run(['python3',str(p/'bench.py'),'screen-'+name+'-'+suffix,'--width','1920','--modules',cfg[variant]['modules']],check=True)
  print('SCREEN_COMPLETE',name,flush=True)
finally:mon.terminate();mon.wait();f.close()

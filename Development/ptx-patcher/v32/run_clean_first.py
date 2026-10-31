"""Finish with a fully serialized first round and conditional repeat."""
from pathlib import Path
import json,time,subprocess,sys,os
p=Path(__file__).resolve().parent
start=time.monotonic()
while True:
 try:
  if len(json.loads((p/'arithmetic.json').read_text()))==48:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 assert time.monotonic()-start<2400
 time.sleep(1)
sys.argv=['run_clean_first.py','clean'];os.environ['V32_DATASET']='clean.json'
import bench as b
for direction,widths in [('forward',[1600,1920]),('reverse',[1920,1600,1280])]:
 for w in widths:
  for v in ['split','up','split_up']:
   order=['baseline',v,v,'baseline'] if direction=='forward' else [v,'baseline','baseline',v]
   for j,version in enumerate(order):b.run(f'clean-{direction}-{v}-{j}',version,w)
raw=json.loads((p/'bench.json').read_text());repair=json.loads((p/'repair.json').read_text());clean=json.loads((p/'clean.json').read_text())
assert len(raw)==72 and len(repair)==12 and len(clean)==60
(p/'excluded-timing.json').write_text(json.dumps([r|{'exclusion_reason':'initial screening overlapped driver compilation / resource queries; entire initial round replaced'} for r in raw],indent=2)+'\n')
(p/'first.json').write_text(json.dumps(clean+repair,indent=2)+'\n')
subprocess.run([sys.executable,str(p/'summarize.py')],check=True)
eligible=json.loads((p/'repeat-eligible.json').read_text())
if eligible:
 env=os.environ.copy();env['V32_DATASET']='repeat.json'
 with (p/'repeat.log').open('w') as f:subprocess.run([sys.executable,str(p/'bench.py'),'repeat',*eligible],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run([sys.executable,str(p/'summarize.py')],check=True)
for script in ['tables.py','validate_data.py','finalize.py']:
 with (p/(script+'.log')).open('w') as f:subprocess.run([sys.executable,str(p/script)],stdout=f,stderr=subprocess.STDOUT,check=True)

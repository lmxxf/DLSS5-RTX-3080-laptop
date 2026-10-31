from pathlib import Path
import json,time,subprocess,sys
p=Path(__file__).resolve().parent
start=time.monotonic()
while True:
 try:
  rows=json.loads((p/'caps.json').read_text())
  if len(rows)==144:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 assert time.monotonic()-start<1800,'caps did not finish'
 time.sleep(1)
for script in ['probes.py','bench_probes.py']:
 with (p/(script+'.log')).open('w') as f:subprocess.run([sys.executable,str(p/script)],stdout=f,stderr=subprocess.STDOUT,check=True)

subprocess.run([sys.executable,str(p/'summarize.py')],check=True)
eligible=json.loads((p/'repeat-eligible.json').read_text())
if eligible:
 with (p/'repeat.log').open('w') as f:subprocess.run([sys.executable,str(p/'bench.py'),'repeat',*eligible],stdout=f,stderr=subprocess.STDOUT,check=True)
 subprocess.run([sys.executable,str(p/'summarize.py')],check=True)

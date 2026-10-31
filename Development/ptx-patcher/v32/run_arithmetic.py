from pathlib import Path
import json,time,subprocess,sys,os
p=Path(__file__).resolve().parent
start=time.monotonic()
while True:
 try:
  if len(json.loads((p/'probe-bench.json').read_text()))==48:break
 except (FileNotFoundError,json.JSONDecodeError):pass
 assert time.monotonic()-start<2400
 time.sleep(1)
for args,log in [(['check_decode.py'],'shift-tests.log'),(['build.py','shift','split_up_shift'],'build-shift.log'),(['audit.py','shift','split_up_shift'],'audit-shift.log'),(['bench.py','timed','shift','split_up_shift'],'arithmetic.log')]:
 env=os.environ.copy();env['V32_DATASET']='arithmetic.json'
 with (p/log).open('w') as f:subprocess.run([sys.executable,str(p/args[0]),*args[1:]],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)

from pathlib import Path
import subprocess,sys,os,json,time,datetime
p=Path(__file__).resolve().parent;events=[]
def run(args,log,env=None):
 start=datetime.datetime.now().isoformat()
 with (p/log).open('w') as f:result=subprocess.run([sys.executable,str(p/args[0]),*args[1:]],env=env,stdout=f,stderr=subprocess.STDOUT)
 events.append({'args':args,'begin':start,'end':datetime.datetime.now().isoformat(),'returncode':result.returncode});(p/'serial-stages.json').write_text(json.dumps(events,indent=2)+'\n');assert result.returncode==0,(args,log)
t=time.monotonic()
while True:
 try:
  if 'phase_guarded_quad_fb23' in json.loads((p/'candidates.json').read_text()):break
 except (FileNotFoundError,json.JSONDecodeError):pass
 assert time.monotonic()-t<1200
 time.sleep(1)
env=os.environ.copy();env['V33_MODE']='remat_call';run(['check_alias.py'],'alias-call.log',env)
run(['audit.py'],'audit-final.log')
run(['prepare_data.py'],'prepare-data.log')
run(['tables.py'],'tables.log')
for stage in ['smoke','probes','timed']:run(['sweep.py',stage],stage+'.log')
run(['summarize.py'],'summary.log')
if json.loads((p/'repeat-eligible.json').read_text()):
 run(['sweep.py','repeat'],'repeat.log');run(['summarize.py'],'summary-repeat.log')
run(['validate.py'],'validation.log')

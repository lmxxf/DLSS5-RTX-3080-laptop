from pathlib import Path
import subprocess,sys,json,datetime
p=Path(__file__).resolve().parent;rows=[]
def run(args):
 start=datetime.datetime.now().isoformat();log=p/(args[0]+('-'+args[1] if len(args)>1 else '')+'.log')
 with log.open('w') as f:r=subprocess.run([sys.executable,str(p/args[0]),*args[1:]],stdout=f,stderr=subprocess.STDOUT)
 rows.append({'args':args,'begin':start,'end':datetime.datetime.now().isoformat(),'returncode':r.returncode});(p/'serial-stages.json').write_text(json.dumps(rows,indent=2)+'\n');assert r.returncode==0,(args,log)
run(['prepare_data.py']);run(['tables.py']);run(['sweep.py','smoke']);run(['sweep.py','timed']);run(['summarize.py'])
if json.loads((p/'repeat-eligible.json').read_text()):run(['sweep.py','repeat']);run(['summarize.py'])
run(['validate.py'])

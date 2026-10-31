from pathlib import Path
import subprocess,datetime,json,sys
p=Path(__file__).resolve().parent
def run(args,tag=None):
 start=datetime.datetime.now().isoformat();r=subprocess.run([sys.executable,str(p/args[0]),*args[1:]],capture_output=True,text=True,encoding='utf-8',errors='replace');record={'tag':tag or ' '.join(args),'args':args,'begin':start,'end':datetime.datetime.now().isoformat(),'returncode':r.returncode,'output':r.stdout+r.stderr};path=p/'execution.json';rows=json.loads(path.read_text()) if path.exists() else [];rows.append(record);path.write_text(json.dumps(rows,indent=2)+'\n');print(record['tag'],r.returncode,flush=True)
 if r.returncode:raise RuntimeError(record['output'])
 return record
if __name__=='__main__':run(sys.argv[1:])

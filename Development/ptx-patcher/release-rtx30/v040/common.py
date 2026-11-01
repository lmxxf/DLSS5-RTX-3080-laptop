from pathlib import Path
import json,hashlib,subprocess,datetime
P=Path(__file__).resolve().parent;ROOT=Path('/mnt/c/DLSS5-5090-dll');OUT=ROOT/'发布打包';STAGE=OUT/'.stage-v0.4.0';TOOLS=ROOT/'release-v040-tools';BACKUP=ROOT/'backups/20261101-v040';CORE=ROOT/'nvngx_dlssnr_sm86_v40.dll';SHA='749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca';OLD='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86';PS='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe';DRIVER=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';META={'README.txt','README.en.txt','DLSS5-RTX30-VERSION.txt','release.json','SHA256SUMS.txt','nvngx_dlssnr.manifest.json'}
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for c in iter(lambda:s.read(8<<20),b''):h.update(c)
 return h.hexdigest()
def read(f):return json.loads(Path(f).read_text(encoding='utf-8-sig'))
def write(f,d):Path(f).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def win(f):
 f=str(Path(f).resolve())
 return 'C:/'+f[7:] if f.startswith('/mnt/c/') else subprocess.check_output(['wslpath','-w',f],text=True).strip()
def run(args,cwd=None,tag=None,timeout=240):
 begin=datetime.datetime.now().astimezone().isoformat();r=subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout);row={'tag':tag or str(args[0]),'args':[str(x) for x in args],'begin':begin,'end':datetime.datetime.now().astimezone().isoformat(),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr};f=P/'execution.json';rows=read(f) if f.exists() else [];rows.append(row);write(f,rows)
 if r.returncode:raise RuntimeError(row)
 return row

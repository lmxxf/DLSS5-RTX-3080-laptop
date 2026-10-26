from pathlib import Path
import json,hashlib,subprocess,datetime,os
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
def run(tag,variant,w,warmup=50,iterations=80):
 variants=json.loads((p/'build-results.json').read_text())['variants'];dll=root/'nvngx_dlssnr_sm86_v2.dll' if variant=='baseline' else Path(variants[variant]['path']);h={1280:720,1600:900,1920:1080}[w]
 outdir=root/'ptx-v21-bench';outdir.mkdir(exist_ok=True);name=f'{tag}-{variant}-{w}';log=p/(name+'.log');out=outdir/(name+'.rgb32');assert not log.exists() and not out.exists(),name
 args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,str(dll).replace('/mnt/c/','C:/'),str(w),str(h),'2',str(warmup),str(iterations),str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 begin=datetime.datetime.now().isoformat()
 with log.open('w') as f:ret=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT).returncode
 meta={'tag':tag,'variant':variant,'width':w,'height':h,'warmup':warmup,'iterations':iterations,'begin':begin,'end':datetime.datetime.now().isoformat(),'returncode':ret,'args':args,'dll_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'output':str(out)}
 (p/(name+'-run.json')).write_text(json.dumps(meta,indent=2)+'\n');assert ret==0,(name,ret);print(name,log.read_text().split('SUMMARY')[-1].strip(),flush=True)
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('tag');a.add_argument('variant');a.add_argument('width',type=int);a=a.parse_args();run(a.tag,a.variant,a.width)

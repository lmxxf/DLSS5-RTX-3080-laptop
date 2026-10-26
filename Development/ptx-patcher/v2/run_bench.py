from pathlib import Path
import subprocess,json,hashlib,datetime,argparse
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');a=argparse.ArgumentParser();a.add_argument('--tag',default='compare');a.add_argument('--warmup',type=int,default=50);a.add_argument('--iterations',type=int,default=80);a=a.parse_args()
paths={'old':root/'nvngx_dlssnr_sm86_fast.dll','new':root/'nvngx_dlssnr_sm86_v2.dll','v7':root/'discord_v7/nvngx_dlssnr_309_v2i8_255_rtx2030_V7.dll'}
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(paths['old'])=='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a'
core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';dest=root/'ptx-v2-bench';dest.mkdir(exist_ok=True)
tele=(p/f'{a.tag}-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=tele)
try:
 for w,h in [(1280,720),(1600,900),(1920,1080)]:
  for round,order in [('forward',['old','new','v7']),('reverse',['v7','new','old'])]:
   for v in order:
    name=f'{a.tag}-{round}-{v}-{w}';log=p/(name+'.log');out=dest/(name+'.rgb32');assert not log.exists() and not out.exists()
    args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,str(paths[v]).replace('/mnt/c/','C:/'),str(w),str(h),'2',str(a.warmup),str(a.iterations),str(out).replace('/mnt/c/','C:/')]
    if w==1280:args+=['sky']
    start=datetime.datetime.now().isoformat()
    with log.open('w') as f:ret=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT).returncode
    end=datetime.datetime.now().isoformat();meta={'variant':v,'width':w,'height':h,'round':round,'args':args,'dll_sha256':sha(paths[v]),'begin':start,'end':end,'returncode':ret,'output':str(out),'warmup':a.warmup,'iterations':a.iterations};(p/(name+'-run.json')).write_text(json.dumps(meta,indent=2)+'\n');assert ret==0,(name,ret)
    print(name,log.read_text().split('SUMMARY')[-1].strip(),flush=True)
finally:mon.terminate();mon.wait();tele.close()

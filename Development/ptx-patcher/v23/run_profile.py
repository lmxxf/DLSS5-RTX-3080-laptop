from pathlib import Path
import subprocess,os,json,sys
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
mode=sys.argv[1] if len(sys.argv)>1 else 'events';widths=list(map(int,sys.argv[2:])) or [1280,1920]
for w in widths:
 h={1280:720,1600:900,1920:1080}[w];tag=os.environ.get('V23_TAG','');name=f'{tag+"-" if tag else ""}{mode}-{w}';trace=root/f'v23-{name}.csv';out=root/f'v23-{name}.rgb32';env=os.environ.copy();env['V23_TRACE']=str(trace).replace('/mnt/c/','C:/')
 env['WSLENV']=env.get('WSLENV','')+':V23_TRACE:V23_EVENTS:V23_SPLIT'
 if mode in ['events','split']:env['V23_EVENTS']='1'
 if mode=='split':env['V23_SPLIT']='1'
 args=[str(root/'nvngx.dll_runner/bench_profile.exe'),core,os.environ.get('V23_PROFILE_DLL',str(root/'nvngx_dlssnr_sm86_v22.dll')).replace('/mnt/c/','C:/'),str(w),str(h),'2','50','20',str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 with (p/f'{name}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90)
 assert r.returncode==0,(name,r.returncode);(p/f'{name}.csv').write_bytes(trace.read_bytes());trace.unlink();print(name,(p/f'{name}.log').read_text().split('SUMMARY')[-1],flush=True)

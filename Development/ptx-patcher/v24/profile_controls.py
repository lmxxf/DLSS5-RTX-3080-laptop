"""Diagnostic per-FB timestamps; speed promotion uses uninstrumented ABBA."""
from pathlib import Path
import os,subprocess,json,re,statistics as st,hashlib,numpy as np,collections,datetime
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');work=root/'ptx-v24-profile';work.mkdir(exist_ok=True);core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';variants={'baseline':{'path':str(root/'nvngx_dlssnr_sm86_v23.dll')}}|json.loads((p/'builds.json').read_text())|json.loads((p/'caps.json').read_text());functions=json.loads((p.parent/'v23/resources.json').read_text())['decode'];fbmap={n:int(fb) for fb,r in functions.items() for n in r['kernels']};rows={};gold=None
order=['baseline','c','abc']+sorted(json.loads((p/'caps.json').read_text()))+['abc-end']
for tag in order:
 v='abc' if tag=='abc-end' else tag;dll=Path(variants[v]['path']);trace=work/f'{tag}.csv';rgb=work/f'{tag}.rgb32';env=os.environ.copy();env['V23_TRACE']=str(trace).replace('/mnt/c/','C:/');env['V23_EVENTS']='1';env['WSLENV']=env.get('WSLENV','')+':V23_TRACE:V23_EVENTS'
 args=[str(root/'nvngx.dll_runner/bench_profile.exe'),core,str(dll).replace('/mnt/c/','C:/'),'1920','1080','2','50','20',str(rgb).replace('/mnt/c/','C:/')]
 with (p/f'profile-{tag}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90)
 assert r.returncode==0,(tag,r.returncode);x=np.fromfile(rgb,np.uint32)
 if gold is None:gold=x.copy()
 diff=int(np.count_nonzero(x!=gold));assert diff==0,(tag,diff);rgb.unlink();frames=collections.defaultdict(list);kept=[];raw=trace.read_bytes()
 for line in raw.decode().splitlines():
  if line.startswith(('KERNEL,','CHAIN,')) and 0<=int(line.split(',')[1])<50:continue
  kept.append(line)
  if not line.startswith('KERNEL,'):continue
  z=line.split(',');frame=int(z[1])
  if frame>=50:frames[frame].append({'FB':fbmap[z[4]],'name':z[4],'gpu_ms':float(z[12]),'grid':list(map(int,z[5:8])),'block':list(map(int,z[8:11]))})
 assert len(frames)==20 and all(len(v)==82 for v in frames.values());(p/f'profile-{tag}.csv').write_text('\n'.join(kept)+'\n');trace.unlink();byfb={}
 for fb in sorted({r['FB'] for rs in frames.values() for r in rs}):
  vals=[sum(r['gpu_ms'] for r in rs if r['FB']==fb) for rs in frames.values()];byfb[str(fb)]={'median_ms':st.median(vals),'mean_ms':st.mean(vals)}
 summary=(p/f'profile-{tag}.log').read_text().split('SUMMARY')[-1];rows[tag]={'variant':v,'DLL_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'output_bitdiff':diff,'raw_csv_sha256':hashlib.sha256(raw).hexdigest(),'retained_rows':len(kept),'warmup_records_pruned':True,'by_FB':byfb,'metrics':{k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',summary)},'warmup':50,'iterations':20};(p/'profile-controls.json').write_text(json.dumps(rows,indent=2)+'\n');print(tag,{fb:round(v['mean_ms'],4) for fb,v in byfb.items() if int(fb) in [1,2,4,5]},flush=True)

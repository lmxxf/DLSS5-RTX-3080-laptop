from pathlib import Path
import subprocess,os,json,hashlib,re,argparse,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;pa=argparse.ArgumentParser();pa.add_argument('--tag',default='regression');pa.add_argument('--geometry');a=pa.parse_args();runs=p/'artifacts/runs'/a.tag;runs.mkdir(parents=True,exist_ok=True)
base=json.loads((p/'phase14-baseline-manifest.json').read_text());modules=p/'artifacts/selected/modules';assert {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in modules.glob('*.hsaco')}==base,'Phase14 native baseline changed'
refs=json.loads((p/'reference-modules.sha256.json').read_text());reference=p/'artifacts/reference/modules';assert {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in reference.glob('*.hsaco')}==refs
manifest=json.loads((p/'input-manifest.json').read_text());prior=p/(a.tag+'-runs.json');allruns=json.loads(prior.read_text()) if a.geometry and prior.exists() else [];failures=[]
def invoke(label,w,h,files,mode):
 out=runs/label/mode;out.mkdir(parents=True,exist_ok=True);assert not list(out.glob('*.rgb32')),'refusing to overwrite prior output'
 env={k:v for k,v in os.environ.items() if not k.startswith(('DLSS5_','NR_'))};env.update(DLSS5_AMPERE_WEIGHTS='0' if mode=='f32' else '1',DLSS5_LAB_COMPACT_ALL='0' if mode=='f32' else '1',DLSS5_LAB_C256_SPLIT='1' if mode=='f32' and w!=1920 else '0')
 if mode=='256':env['DLSS5_LAB_ATTN400']='0'
 log=p/f'{a.tag}-{label}-{mode}.log';assert not log.exists(),log
 cmd=[str(p/'artifacts/host/frame_runner'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(reference if mode=='f32' else modules),str(w),str(h),str(out)]+files
 with log.open('w') as f:ret=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 text=log.read_text();resources={}
 for line in text.splitlines():
  t=line.split()
  if len(t)==7 and t[0]=='RESOURCE':resources[t[1]]=dict(zip(['calls','block','regs','lmem','smem'],map(int,t[2:])))
 row={'label':label,'mode':mode,'processing':[w,h],'returncode':ret.returncode,'log':str(log),'output_dir':str(out),'resources':resources,'input_SHA256':[hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files],'flags':{k:v for k,v in env.items() if k.startswith(('DLSS5_','NR_'))},'runner_sha256':hashlib.sha256((p/'artifacts/host/frame_runner').read_bytes()).hexdigest()}
 if ret.returncode==0:
  assert 'resource_output_bitdiff=0' in text
  if mode!='f32':assert len(resources)==32 and all(t['lmem']==0 for t in resources.values()),row
  row['frames']=[dict(zip(['frame','input','invalid','repeat_bitdiff'],map(int,m))) for m in re.findall(r'FRAME index=(\d+) input=(\d+) invalid=(\d+) repeat_bitdiff=(\d+)',text)]
  assert all(f['invalid']==f['repeat_bitdiff']==0 for f in row['frames'])
  row['output_sha256']=[hashlib.sha256((out/f'{i}.rgb32').read_bytes()).hexdigest() for i in range(len(files))]
 else:failures.append({'label':label,'mode':mode,'log':str(log),'returncode':ret.returncode})
 allruns.append(row);(p/(a.tag+'-runs.json')).write_text(json.dumps(allruns,indent=2)+'\n');return row
# Calibrate the reference chain BEFORE using new image metrics.
cal=[]
for w,h in ([] if a.geometry else [(1600,1024),(1920,1152),(1280,768)]):
 file=str(p/f'artifacts/inputs/baseline-{w}.rgba32')
 for mode in ['f32','400']:
  row=invoke(f'baseline-{w}',w,h,[file],mode);assert row['returncode']==0,'calibration process failure'
  expected=(r/'phase14/artifacts/gold/f32-720p-1280x768.rgb32' if w==1280 else r/f'phase1/artifacts/outputs/f32-{w}.rgb32') if mode=='f32' else r/f'phase14/artifacts/outputs/default400-{w}.rgb32'
  x=np.fromfile(Path(row['output_dir'])/'0.rgb32',np.uint32);y=np.fromfile(expected,np.uint32);diff=int(np.count_nonzero(x!=y));assert diff==0,(w,mode,diff)
  cal.append({'width':w,'mode':mode,'gold_bitdiff':diff,'gold_sha256':hashlib.sha256(expected.read_bytes()).hexdigest()})

if cal:(p/'calibration.json').write_text(json.dumps(cal,indent=2)+'\n')
else:assert all(x['gold_bitdiff']==0 for x in json.loads((p/'calibration.json').read_text()))
for geo in manifest['geometries']:
 label=geo['geometry'];
 if a.geometry and a.geometry!=label:continue
 w,h=geo['processing'];files=[i['file'] for i in geo['inputs']]
 for mode in ['400','256','f32']:invoke(label,w,h,files,mode)
(p/(a.tag+'-failures.json')).write_text(json.dumps(failures,indent=2)+'\n');print('Completed',len(allruns),'runs; failures',len(failures));
if failures:print(failures)

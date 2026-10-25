from diag15b_paths import ROOT
from pathlib import Path
import subprocess,os,json,hashlib
p=Path(__file__).resolve().parent;r=p.parent;root=ROOT;rows=[]
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 w,h=case['processing']
 for mode in ['native','f32']:
  out=root/'traces'/case['case']/mode;out.mkdir(parents=True,exist_ok=True);assert not (out/'0.rgb32').exists(),'refusing overwrite'
  env={k:v for k,v in os.environ.items() if not k.startswith(('DLSS5_','NR_'))};env.update(DLSS5_AMPERE_WEIGHTS='1' if mode=='native' else '0',DLSS5_LAB_COMPACT_ALL='1' if mode=='native' else '0',DLSS5_LAB_C256_SPLIT='1' if mode=='f32' else '0',DLSS5_DIAG15B_TRACE=str(out))
  modules=p/'artifacts/selected/modules' if mode=='native' else root/'reference'
  log=p/f'diag15b-{case["case"]}-{mode}.log'
  with log.open('w') as f:ret=subprocess.run([str(root/'host/frame_runner'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(modules),str(w),str(h),str(out),case['input_file']],env=env,stdout=f,stderr=subprocess.STDOUT)
  assert ret.returncode==0,(mode,log)
  source=hashlib.sha256((out/'working-input.bin').read_bytes()).hexdigest();assert source==case['input_sha256'],'tap saw wrong input'
  sha=hashlib.sha256((out/'0.rgb32').read_bytes()).hexdigest();expected=case.get('frozen_output_'+mode)
  if expected:assert sha==expected,(case['case'],mode,'tap changed frozen output')
  row={'case':case['case'],'mode':mode,'working_input_sha256':source,'output_sha256':sha,'frozen_output_match':sha==expected if expected else None,'log':str(log),'trace':str(out),'returncode':ret.returncode};rows.append(row);print(row,flush=True)
(p/'diag15b-runs.json').write_text(json.dumps(rows,indent=2)+'\n')

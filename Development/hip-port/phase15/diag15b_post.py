from diag15b_paths import ROOT
from pathlib import Path
import os,subprocess,json,hashlib
p=Path(__file__).resolve().parent;root=ROOT;rows=[]
for c in json.loads((p/'diag15b-inputs.json').read_text()):
 w,h=c['processing']
 for mode in ['native','f32']:
  out=root/'post'/c['case']/mode;out.mkdir(parents=True,exist_ok=True);assert not (out/'0.rgb32').exists()
  env={k:v for k,v in os.environ.items() if not k.startswith(('DLSS5_','NR_'))};env.update(DLSS5_AMPERE_WEIGHTS='1' if mode=='native' else '0',DLSS5_LAB_COMPACT_ALL='1' if mode=='native' else '0',DLSS5_LAB_C256_SPLIT='1' if mode=='f32' else '0',DLSS5_DIAG15B_TRACE=str(out),DLSS5_DIAG15B_POST='1',DLSS5_DIAG15B_POST_ONLY='1');mods=p/'artifacts/selected/modules' if mode=='native' else root/'reference';log=p/f'diag15b-post-{c["case"]}-{mode}.log'
  if mode=='f32':env['DLSS5_DIAG15B_NATIVE_POST_DIR']=str(root/'post'/c['case']/'native')
  with log.open('w') as f:ret=subprocess.run([str(root/'host/frame_runner'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(mods),str(w),str(h),str(out),c['input_file']],env=env,stdout=f,stderr=subprocess.STDOUT)
  assert ret.returncode==0,log;assert '15B_POST_REPLAY bitdiff=0 ' in log.read_text(),'feature replay not equivalent'
  assert hashlib.sha256((out/'working-input.bin').read_bytes()).hexdigest()==c['input_sha256'];expected=hashlib.sha256((root/'traces'/c['case']/mode/'0.rgb32').read_bytes()).hexdigest();assert hashlib.sha256((out/'0.rgb32').read_bytes()).hexdigest()==expected
  rows.append({'case':c['case'],'mode':mode,'original_vs_feature_replay_bitdiff':0,'main_output_SHA_unchanged':True})
(p/'diag15b-post-verification.json').write_text(json.dumps(rows,indent=2)+'\n');print('Verified feature replay equivalence on all8 runs')

from diag15b_paths import ROOT
from pathlib import Path
import numpy as np,json,hashlib
from reference import decode
p=Path(__file__).resolve().parent;root=ROOT;rows={};cold=[]
for c in json.loads((p/'diag15b-inputs.json').read_text()):
 name=c['case'];base=root/'post'/name;rr={}
 for channels in [64,128]:
  y=decode(np.fromfile(base/'native'/f'wave{channels}-out.bin',np.uint8)).astype(float);b=decode(np.fromfile(base/'f32'/f'wave{channels}-out.bin',np.uint8)).astype(float);m=decode(np.fromfile(base/'f32'/f'wave{channels}-cross.bin',np.uint8)).astype(float);loc=y-m;up=m-b;total=y-b
  rr[f'C{channels}_first_encoder']={'local_same_input_MSE':float(np.mean(loc*loc)),'upstream_input_MSE':float(np.mean(up*up)),'cross_term':float(2*np.mean(loc*up)),'total_MSE':float(np.mean(total*total))}
 # Check that post captured low/skip really are the named main graph stages.
 for mode in ['native','f32']:
  for a,b in [('post-low','block69'),('post-skip','block0')]:assert hashlib.sha256((base/mode/(a+'.bin')).read_bytes()).digest()==hashlib.sha256((root/'traces'/name/mode/(b+'.bin')).read_bytes()).digest()
 rows[name]=rr
 if name=='canonical720':
  old=[('f32',base/'f32/prepare-qkv.bin',p/'artifacts/gold-capture/0-qkv.bin'),('native',base/'native/prepare-qkv.bin',p/'artifacts/actual-qkv/phase12.bin')]
  for mode,a,b in old:
   cold.append({'mode':mode,'current_Prepare_QKV_SHA':hashlib.sha256(a.read_bytes()).hexdigest(),'historical_QKV_SHA':hashlib.sha256(b.read_bytes()).hexdigest(),'byte_identical':a.read_bytes()==b.read_bytes(),'actual_frozen_input_QKV_SHA':hashlib.sha256((root/'traces'/name/mode/'qkv-0-out.bin').read_bytes()).hexdigest()})
(p/'diag15b-branches.json').write_text(json.dumps({'cases':rows,'cold_capture_provenance_check':cold,'scope':'Separate same-input F32 operator replays; original network tensors read-only. MSE cross terms included.'},indent=2)+'\n');print(rows);print(cold)

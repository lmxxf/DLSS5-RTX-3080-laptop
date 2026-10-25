from pathlib import Path
import numpy as np,json,hashlib,shutil
r=Path(__file__).resolve().parents[1];p=r/'phase14';rows={}
def read(v,w):return np.fromfile(p/f'artifacts/outputs/{v}-{w}.rgb32',np.float32)
for w,h,vh in [(1280,768,720),(1600,1024,900),(1920,1152,1080)]:
 a=read('fixed-quick',w);g=read('gold-f32',w);old=np.fromfile(r/f'phase12/artifacts/outputs/selected-{w}.rgb32',np.float32)
 assert np.isfinite(a).all() and np.isfinite(g).all();d=a.reshape(h,w,3)[:vh].astype(float)-g.reshape(h,w,3)[:vh]
 row={'full_vs_phase12_bitdiff':int(np.count_nonzero(a.view(np.uint32)!=old.view(np.uint32))),'invalid':0,'visible_psnr_peak1':float(-10*np.log10(np.mean(d*d))),'visible_maxabs':float(np.max(abs(d))),'F32_sha256':hashlib.sha256(g.tobytes()).hexdigest(),'FP16_sha256':hashlib.sha256(a.tobytes()).hexdigest()}
 if w!=1280:
  gold=np.fromfile(r/f'phase1/artifacts/outputs/f32-{w}.rgb32',np.uint32);assert np.array_equal(g.view(np.uint32),gold);assert np.array_equal(read('f32-control',w).view(np.uint32),gold);assert row['full_vs_phase12_bitdiff']==0
  row['existing_F32_gold_bitdiff']=0
 else:
  assert row['full_vs_phase12_bitdiff']>0;assert np.array_equal(g.view(np.uint32),read('gold-f32-400',w).view(np.uint32));assert np.array_equal(a.view(np.uint32),read('fixed-quick-400',w).view(np.uint32));row['correct256_vs400_full_output_bitdiff']=0
 rows[w]=row
folder=p/'artifacts/gold';folder.mkdir(exist_ok=True);out=folder/'f32-720p-1280x768.rgb32';src=p/'artifacts/outputs/gold-f32-1280.rgb32'
if out.exists():assert out.read_bytes()==src.read_bytes()
else:shutil.copy2(src,out)
(p/'initial-quality.json').write_text(json.dumps(rows,indent=2)+'\n')
(p/'gold-manifest.json').write_text(json.dumps({'name':'Phase14 corrected720 Small31 Style1 F32 gold','processing':[1280,768],'visible':[1280,720],'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_modules':json.loads((p/'f32-fixed-modules.sha256.json').read_text()),'calibration_900_1080_bitdiff':[0,0],'correct256_vs400_full_output_bitdiff':0,'rounding':'F32 TensorCore accum; sourceVIT_FAST_NUM15 and actual rcp.approx; FP8/RTZ behavior unchanged; AMPERE_WEIGHTS0 legacyF32 packing.'},indent=2)+'\n')
print(json.dumps(rows,indent=2))

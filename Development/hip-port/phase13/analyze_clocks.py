from pathlib import Path
import numpy as np,json
p=Path(__file__).resolve().parent;rows={}
for f in (p/'artifacts/clocks-steady').glob('*.clock'):
 a=np.fromfile(f,np.uint64).reshape(2,1024,64)[int('prefix' in f.name)]
 ok=(a[:,:32]!=0).all(axis=1);a=a[ok].astype(np.int64);assert len(a)>0;row={}
 for n,i,j in [('prefix/merge-input',0,1),('FFN-expand-act-contract',1,2),('feature-pack-QKV-norm',2,3),('QK-softmax',4,5),('AV-pack',5,6),('project-residual',6,7)]:
  vals=np.stack([a[:,qt*8+j]-a[:,qt*8+i] for qt in range(4)],1);row[n]={'median_cycles_per_qt':float(np.median(vals)),'p10':float(np.percentile(vals,10)),'p90':float(np.percentile(vals,90))}
 if (a[:,33]!=0).all():row['tail']={'median_cycles':float(np.median(a[:,33]-a[:,32]))}
 row['samples']=len(a);rows[f.stem]=row
 # Compiler emits a return before clock33 on Prefix; no tail number is invented.
a=np.fromfile(p/'artifacts/outputs/clock-steady-1920.rgb32',np.uint32);b=np.fromfile(p.parent/'phase12/artifacts/outputs/selected-1920.rgb32',np.uint32);assert np.array_equal(a,b)
(p/'clock-results.json').write_text(json.dumps({'diagnostic_output_bitdiff':0,'cycles':rows,'limitations':'Sampling/bar.warp/global writes perturb scheduling; not a hardware stall counter or uninstrumented performance estimate. Prefix tail return precedes marker33.'},indent=2)+'\n');print(json.dumps(rows,indent=2))

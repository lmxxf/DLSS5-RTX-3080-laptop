from pathlib import Path
import numpy as np,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase13'
# Same Host graph, different math backend. Shapes of padded deep stages are read from allocations.
formats={'pre-down':'fp8','block0':'fp8','block4':'fp8','block4-down':'fp8','block5':'fp8','block8':'half','block9':'fp8','block14':'half','block15':'fp8','block22':'float','block23':'fp8','block30':'float','head':'fp8',**{f'block{x}':'fp8' for x in range(31,39)},'block39':'fp8','block40':'fp8','block47':'fp8','block48':'fp8','block55':'fp8','block56':'fp8','block61':'fp8','block62':'fp8','block65':'float','block69':'fp8','block70':'float'}
def read(f,kind):
 if kind=='fp8':
  u=np.fromfile(f,np.uint8);a=u&127;return np.where(u&128,-1.,1.)*np.where(a<8,a.astype(float)*2**-9,(1.+(a&7).astype(float)/8)*np.exp2((a>>3).astype(float)-7))
 return np.fromfile(f,np.float16 if kind=='half' else np.float32).astype(float)
rows={};lines=['# Layer boundary comparison','','All diagnostic stage taps preserve output; graph gates unchanged. FP8/half/float formats follow Host allocation contracts, not filename extensions. Padding/inter-byte outputs without valid float materialization excluded.','', '| Width | Stage | Type | Bytes F16/F32 | RMSE | Maxabs | Relative RMSE |','|---|---|---|---:|---:|---:|---:|']
for w in [1280,1600,1920]:
 rows[w]={}
 for name,fmt in formats.items():
  f=p/f'artifacts/traces/phase12-{w}/{name}.bin';g=p/f'artifacts/traces/f32-{w}/{name}.bin'
  if not f.exists() or not g.exists():continue
  formats_here=[fmt,fmt]
  if w==1600 and name in ['block23','block39','block40','block47']:formats_here=['float','float']
  if name=='head' or name in [f'block{x}' for x in range(31,39)]:
   n={1280:240,1600:448,1920:640}[w]
   formats_here=['fp8' if x.stat().st_size==n*1024 else 'float' for x in [f,g]]
  a,b=read(f,formats_here[0]),read(g,formats_here[1]);fmt='/'.join(formats_here)
  row={'dtype':fmt,'bytes':[f.stat().st_size,g.stat().st_size],'sha256':[hashlib.sha256(f.read_bytes()).hexdigest(),hashlib.sha256(g.read_bytes()).hexdigest()]}
  if a.size==b.size:
   d=a-b;row.update(rmse=float(np.sqrt(np.mean(d*d))),maxabs=float(np.max(abs(d))),relative_rmse=float(np.sqrt(np.mean(d*d))/max(np.sqrt(np.mean(b*b)),1e-20)),invalid=int(np.count_nonzero(~np.isfinite(a))+np.count_nonzero(~np.isfinite(b))))
   lines.append(f'| {w} | {name} | {fmt} | {row["bytes"]} | {row["rmse"]:.6g} | {row["maxabs"]:.6g} | {row["relative_rmse"]:.6g} |')
  rows[w][name]=row
 # Prove tapping does not change the chain output against earlier untapped dumps.
 for kind,ref in [('phase12',r/f'phase12/artifacts/outputs/selected-{w}.rgb32'),('f32',r/f'phase12/artifacts/outputs/f32-paired-{w}.rgb32')]:
  a=np.fromfile(p/f'artifacts/outputs/trace-{kind}-{w}.rgb32',np.uint32);b=np.fromfile(ref,np.uint32);assert np.array_equal(a,b),(w,kind)
(p/'layer-comparison.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'layer-comparison.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

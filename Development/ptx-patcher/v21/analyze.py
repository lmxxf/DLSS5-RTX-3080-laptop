from pathlib import Path
import json,re,hashlib,numpy as np
p=Path(__file__).resolve().parent;rows={};refs={}
metas=[(f,json.loads(f.read_text())) for f in sorted(p.glob('*-run.json'))]
for f,m in metas:
 if m['variant']=='baseline' and m['width'] not in refs:refs[m['width']]=Path(m['output'])
for f,m in metas:
 path=Path(m['output']);ref=refs[m['width']];a=np.fromfile(path,np.float32);b=np.fromfile(ref,np.float32);assert a.size==b.size
 bitdiff=int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)));delta=a.astype(float)-b.astype(float);mse=float(np.mean(delta**2));invalid=int(np.count_nonzero(~np.isfinite(a)));s=f.with_name(f.name.replace('-run.json','.log')).read_text();r={'variant':m['variant'],'width':m['width'],'tag':m['tag'],'bitdiff':bitdiff,'PSNR_peak1':-10*np.log10(mse) if mse else 999.,'maxabs':float(np.max(abs(delta))),'invalid':invalid,'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 assert invalid==0,(f,invalid)
 for k in ['gpu_median_ms','gpu_min_ms','wall_median_ms']:r[k]=float(re.search(k+r'=([\d.]+)',s)[1])
 if m['width']==1280:
  image=a.reshape(m['height'],m['width'],3);d=(image[:,:,0]-image[:,:,1]).mean(1);hf=d[1:-1]-(d[:-2]+d[2:])*.5;r['sky']={'sign_changes':int(np.count_nonzero(np.diff(np.sign(d)))),'hf_rms':float(np.sqrt(np.mean(hf**2)))}
 rows[f.stem.replace('-run','')]=r
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# V2.1 cap controls','','Preset2 / Style1, same bench_sky;50warmup/80iter, default DVFS. 720p sky,900p/1080p deterministic scene. Full output against same-tier fresh V2 baseline.','', '| Tag | Variant | Width | GPU min /median ms | Wall median | bitdiff |','|---|---|---:|---:|---:|---:|']
for n,r in rows.items():lines.append(f'| {r["tag"]} | {r["variant"]} | {r["width"]} | {r["gpu_min_ms"]:.3f} /{r["gpu_median_ms"]:.3f} | {r["wall_median_ms"]:.3f} | {r["bitdiff"]} |')
(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

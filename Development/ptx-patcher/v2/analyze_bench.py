from pathlib import Path
import json,re,itertools,hashlib,argparse,numpy as np
p=Path(__file__).resolve().parent;arg=argparse.ArgumentParser();arg.add_argument('--tag',default='compare');tag=arg.parse_args().tag;rows={};arrays={}
for f in sorted(p.glob(tag+'-*-run.json')):
 m=json.loads(f.read_text());s=f.with_name(f.name.replace('-run.json','.log')).read_text();o=Path(m['output']);w,h=m['width'],m['height'];a=np.fromfile(o,np.float32).reshape(h,w,3);name=f.stem.replace('-run','');arrays[name]=a
 r={'variant':m['variant'],'round':m['round'],'width':w,'height':h,'output_sha256':hashlib.sha256(o.read_bytes()).hexdigest(),'output_bytes':o.stat().st_size,'invalid':int(np.count_nonzero(~np.isfinite(a)))}
 for k in ['gpu_median_ms','gpu_min_ms','wall_median_ms','nonfinite']:r[k]=float(re.search(k+r'=([\d.]+)',s)[1])
 assert r['invalid']==r['nonfinite']==0
 if w==1280:
  d=(a[:,:,0]-a[:,:,1]).mean(1);hf=d[1:-1]-(d[:-2]+d[2:])*.5;r['sky']={'sign_changes':int(np.count_nonzero(np.diff(np.sign(d)))),'hf_rms':float(np.sqrt(np.mean(hf**2)))}
 rows[name]=r
pairs={}
for w in [1280,1600,1920]:
 for rnd in ['forward','reverse']:
  for v,u in itertools.combinations(['old','new','v7'],2):
   a=arrays[f'{tag}-{rnd}-{v}-{w}'];b=arrays[f'{tag}-{rnd}-{u}-{w}'];delta=a.astype(float)-b.astype(float);mse=float(np.mean(delta**2));pairs[f'{rnd}-{w}-{v}-vs-{u}']={'psnr_peak1':-10*np.log10(mse) if mse else 999.,'maxabs':float(np.max(abs(delta))),'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)))}
 for v in ['old','new','v7']:
  a=arrays[f'{tag}-forward-{v}-{w}'];b=arrays[f'{tag}-reverse-{v}-{w}'];delta=a.astype(float)-b.astype(float);mse=float(np.mean(delta**2));pairs[f'repeat-{w}-{v}']={'psnr_peak1':-10*np.log10(mse) if mse else 999.,'maxabs':float(np.max(abs(delta))),'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)))}
(p/'bench-results.json').write_text(json.dumps({'runs':rows,'comparisons':pairs},indent=2)+'\n')
lines=['# Route B V2 same-round DLL comparison','','Preset2 / Style1; 50warmup/80iter, 720p sky /900p and1080p deterministic scene; default DVFS. forward old→new→V7, reverse V7→new→old. GPU hardware timestamps, wall kept separately.','', '| Round | Width | DLL | GPU min /median ms | Wall median | Sky sign changes /HF RMS |','|---|---:|---|---:|---:|---|']
for n,r in rows.items():
 sky=r.get('sky');ss=f'{sky["sign_changes"]} /{sky["hf_rms"]:.9f}' if sky else '—';lines.append(f'| {r["round"]} | {r["width"]} | {r["variant"]} | {r["gpu_min_ms"]:.3f} /{r["gpu_median_ms"]:.3f} | {r["wall_median_ms"]:.3f} | {ss} |')
lines+=['','PSNR peak=1 in bench output RGB. Pairwise distance is not absolute model quality; original DLL requires newer hardware and is not run on sm86.','', '| Pair | PSNR dB | maxabs | Bit differences |','|---|---:|---:|---:|']
for n,r in pairs.items():lines.append(f'| {n} | {r["psnr_peak1"]:.6f} | {r["maxabs"]:.9f} | {r["bitdiff"]} |')
(p/'bench-results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

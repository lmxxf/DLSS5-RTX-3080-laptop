from pathlib import Path
import json,csv,datetime,re,hashlib,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');rows=json.loads((p/'results.json').read_text());assert len(rows)==37,len(rows)
assert all(x['bitdiff']==x['invalid']==0 for x in rows.values())
selected=json.loads((p/'selected.json').read_text());out=root/'nvngx_dlssnr_sm86_v21.dll';assert hashlib.sha256(out.read_bytes()).hexdigest()==selected['sha256'];assert hashlib.sha256((root/'nvngx_dlssnr_sm86_v2.dll').read_bytes()).hexdigest()=='737af93c2843fe18462c39da36a0a482e4d410493bed0e178fecabf526880f74'
manifest=json.loads(out.with_suffix('.manifest.json').read_text());assert len(manifest)==15 and all(x[1]=='inline' for x in manifest);(p/'pe-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
finalrows={n:r for n,r in rows.items() if r['tag'] in ['forward','reverse']};assert len(finalrows)==24
for r in finalrows.values():
 if r['width']==1280:assert r['sky']['sign_changes']==0
samples=[]
for f in p.glob('*-telemetry.csv'):
 for a in list(csv.reader(f.open()))[1:]:
  try:samples.append((datetime.datetime.strptime(a[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',v)[0]) for v in a[2:]]))
  except (ValueError,TypeError):pass
tele={}
for f in p.glob('*-run.json'):
 m=json.loads(f.read_text());a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);ss=[r for r in samples if a<=r[0]<=b and r[-1]>=90];tele[f.stem]={'util90_samples':len(ss),**{k:float(np.median([r[i] for r in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry-summary.json').write_text(json.dumps(tele,indent=2)+'\n')
v={'selected':selected,'formal_compare_runs':24,'exploratory_scan_runs':13,'warmup':50,'iterations':80,'all_37_full_outputs_V2_bitdiff':0,'invalid':0,'sky_sign_changes':0,'final_source_build_O4':15,'all_original_slots':True,'measured_and_rebuilt_SHA_identical':True,'V2_preserved':True,'graph_weights_arithmetic':'unchanged; only existing .maxnreg literals changed','all_kernel_stack_zero':False,'not_selected':['all255: extra FB01/02 relaxed caps slower','c256168/255 alone: no reliable frame benefit'],'external_deployment':False,'push':False};(p/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
lines=['# V2 → recommended V2.1, paired formal runs','','GPU min/median and Wall are from the same run; default DVFS. No V7 rerun this phase.','', '| Width | Round | V2 GPU min /median | V2.1 GPU min /median | V2 Wall | V2.1 Wall | Median speed ratio |','|---|---|---:|---:|---:|---:|---:|']
for w in [1280,1600,1920]:
 for tag in ['forward','reverse']:
  a=rows[f'{tag}-baseline-{w}'];b=rows[f'{tag}-hot255-{w}'];lines.append(f'| {w} | {tag} | {a["gpu_min_ms"]:.3f} /{a["gpu_median_ms"]:.3f} | {b["gpu_min_ms"]:.3f} /{b["gpu_median_ms"]:.3f} | {a["wall_median_ms"]:.3f} | {b["wall_median_ms"]:.3f} | {a["gpu_median_ms"]/b["gpu_median_ms"]:.4f}× |')
(p/'final-results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

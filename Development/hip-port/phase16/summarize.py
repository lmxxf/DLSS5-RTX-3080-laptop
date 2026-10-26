from pathlib import Path
import json,csv,re,datetime,numpy as np,hashlib
p=Path(__file__).resolve().parent
rows=json.loads((p/'results.json').read_text());samples=[]
for f in p.glob('*-telemetry.csv'):
 for a in list(csv.reader(f.open()))[1:]:
  try:samples.append((datetime.datetime.strptime(a[0],'%Y/%m/%d %H:%M:%S.%f'),a[1].strip(),*[float(re.search(r'[\d.]+',v)[0]) for v in a[2:]]))
  except (ValueError,TypeError):pass
out={}
for f in p.glob('*-run.json'):
 m=json.loads(f.read_text());v=m['variant'];w=m['width']
 if 'abba' not in v:continue
 a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);ss=[s for s in samples if a<=s[0]<=b and s[-1]>=90]
 out[f.stem]={'begin':m['begin'],'end':m['end'],'util90_samples':len(ss),**{k:float(np.median([s[i] for s in ss])) if ss else None for k,i in [('temp_c',2),('power_w',3),('sm_mhz',4),('mem_mhz',5)]}}
(p/'telemetry-summary.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# ABBA summary','','Each row averages two run medians only for a compact comparison; raw min/median/wall/profile stay paired in results.md. Default DVFS; no equal-clock causal claim.','', '| Round | Width | A1 | B1 | B2 | A2 | Mean median change B-A ms |','|---|---:|---:|---:|---:|---:|---:|']
for tag in ['tail-abba','confirm-abba']:
 for w in ['1280','1600','1920']:
  vals=[rows[v+'-'+tag][w]['gpu_median'] for v in ['baseline-a','tail-b','tail-b2','baseline-a2']];delta=(vals[1]+vals[2]-vals[0]-vals[3])/2
  lines.append(f'| {tag} | {w} | '+ ' | '.join(f'{v:.3f}' for v in vals)+f' | {delta:+.4f} |')
lines+=['','## Four ViT kernels, independent instrumented frames','','| Round | Width | Kernel | A1 | B1 | B2 | A2 |','|---|---:|---|---:|---:|---:|---:|']
for tag in ['tail-abba','confirm-abba']:
 for w in ['1280','1600','1920']:
  for n in ['vit_expand_blocked_fp8_frag_bytein_w16','vit_stream_contract_frag_bstream_bout','vit_stream_project_n64_bb_bout','vit_stream_qkv_frag_bin_w5f8']:
   vals=[rows[v+'-'+tag][w]['kernels'][n]['ms'] for v in ['baseline-a','tail-b','tail-b2','baseline-a2']];lines.append(f'| {tag} | {w} | {n} | '+' | '.join(f'{v:.6f}' for v in vals)+' |')
(p/'summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:13]))

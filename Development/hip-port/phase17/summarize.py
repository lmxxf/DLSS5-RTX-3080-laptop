from pathlib import Path
import json,csv,re,datetime,numpy as np,ctypes as C
p=Path(__file__).resolve().parent;x=json.loads((p/'results.json').read_text());lines=['# Phase17 ABBA summary','','Mean of two run medians is a compact comparison only; raw min/median/Wall/profile remain grouped in results.md.','', '| Width | A1 | B1 | B2 | A2 | A mean | B mean | Speed ratio |','|---|---:|---:|---:|---:|---:|---:|---:|'];benefit={}
for w in ['1280','1600','1920']:
 v=[x[n+'-nc-abba'][w]['gpu_median'] for n in ['baseline-a','candidate-b','candidate-b2','baseline-a2']];a=(v[0]+v[3])/2;b=(v[1]+v[2])/2;benefit[w]={'baseline_median_mean':a,'candidate_median_mean':b,'speed_ratio':a/b,'time_reduction_percent':100*(1-b/a)};lines.append(f'| {w} | '+ ' | '.join(f'{t:.3f}' for t in v)+f' | {a:.4f} | {b:.4f} | {a/b:.4f}× |')
lines+=['','## Six C32 independent instrumented profiles','','| Width | Kernel | A1 | B1 | B2 | A2 |','|---|---|---:|---:|---:|---:|']
for w in ['1280','1600','1920']:
 for n in x['baseline-a-nc-abba'][w]['kernels']:
  if n.startswith('c32_wave1_'):
   vals=[x[v+'-nc-abba'][w]['kernels'][n]['ms'] for v in ['baseline-a','candidate-b','candidate-b2','baseline-a2']];lines.append(f'| {w} | {n} | '+' | '.join(f'{t:.6f}' for t in vals)+' |')
(p/'summary.md').write_text('\n'.join(lines)+'\n');(p/'benefit.json').write_text(json.dumps(benefit,indent=2)+'\n')
samples=[]
for f in p.glob('*-telemetry.csv'):
 for a in list(csv.reader(f.open()))[1:]:
  try:samples.append((datetime.datetime.strptime(a[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',q)[0]) for q in a[2:]]))
  except (ValueError,TypeError):pass
tele={}
for f in p.glob('*-run.json'):
 m=json.loads(f.read_text());a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);ss=[q for q in samples if a<=q[0]<=b and q[-1]>=90];tele[f.stem]={'util90_samples':len(ss),**{k:float(np.median([q[i] for q in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry-summary.json').write_text(json.dumps(tele,indent=2)+'\n')
log=(p/'candidate-b-nc-abba-1920.log').read_text();weights=[{'key':m[1],'attention':int(m[2]),'old_bytes':int(m[3]),'new_bytes':int(m[4]),'appended_bytes':int(m[5])} for m in re.finditer(r'C32_HALF_WEIGHT key=(\S+) attention=(\d+) old_bytes=(\d+) new_bytes=(\d+) appended_bytes=(\d+)',log)];assert len(weights)==12
old=sum(q['old_bytes'] for q in weights);new=sum(q['new_bytes'] for q in weights)
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');assert d.cuInit(0)==0;cache=C.c_int();assert d.cuDeviceGetAttribute(C.byref(cache),38,0)==0
(p/'weights.json').write_text(json.dumps({'weights':weights,'old_total_upload_bytes':old,'new_total_upload_bytes':new,'added_bytes':new-old,'old_FP8_matrix_bytes':6*(4096+4096+1536+4096),'new_FP16_matrix_bytes':6*(4096+4096+1536+4096)*2,'L2_capacity_bytes':cache.value,'residency_and_cache_hits':'not measured; capacity fit does not prove100percent residency','all_weights_upload_summary':re.search(r'C512_W16_SUMMARY.*',log)[0]},indent=2)+'\n');print('\n'.join(lines[:10]))

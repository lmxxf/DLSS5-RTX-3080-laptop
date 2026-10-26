from pathlib import Path
import json,re,numpy as np,hashlib
p=Path(__file__).resolve().parent;r=p.parent;dims={1280:(768,720),1600:(1024,900),1920:(1152,1080)};rows={};summary={}
def metric(a,b):
 d=a.astype(float)-b.astype(float);m=float(np.mean(d*d));return {'PSNR_peak1':float(-10*np.log10(m)) if m else 999.,'maxabs':float(np.max(abs(d))),'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)))}
for f in sorted(p.glob('*-run.json')):
 m=json.loads(f.read_text());w=m['width'];n=m['variant'];s=f.with_name(f.name.replace('-run.json','.log')).read_text();h,vh=dims[w];a=np.fromfile(p/f'artifacts/outputs/{n}-{w}.rgb32',np.float32).reshape(h,w,3);ref=np.fromfile(r/f'phase19/artifacts/outputs/candidate-b-m3-{w}.rgb32',np.float32).reshape(h,w,3);goldpath=r/'phase14/artifacts/gold/f32-720p-1280x768.rgb32' if w==1280 else r/f'phase1/artifacts/outputs/f32-{w}.rgb32';gold=np.fromfile(goldpath,np.float32).reshape(h,w,3);kernels={}
 for line in s.splitlines():
  q=line.split()
  if len(q)==10 and q[1].isdigit():kernels[q[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,q[1:])))
 val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);gpu=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s)
 rows[f.stem.replace('-run','')]={'width':w,'variant':n,'gpu_min':float(gpu[2]),'gpu_median':float(gpu[1]),'wall_median':float(wall[1]),'profile_total':float(re.search(r'PROFILE_TOTAL ([\d.]+)',s)[1]),'vs_Phase19':metric(ref[:vh],a[:vh]),'vs_F32gold':metric(gold[:vh],a[:vh]),'Phase19_vs_F32gold':metric(gold[:vh],ref[:vh]),'invalid':int(val[1]),'first_last':int(val[2]),'LMem0':len(kernels)==32 and all(x['lmem']==0 for x in kernels.values()),'kernels':kernels,'output_sha256':hashlib.sha256(a.tobytes()).hexdigest()}
 assert rows[f.stem.replace('-run','')]['invalid']==0 and rows[f.stem.replace('-run','')]['first_last']==0
for w in dims:
 names=[part+'-'+str(w) for part in ['baseline-a','candidate-b','candidate-b2','baseline-a2']]
 if not all(n in rows for n in names):continue
 rr=[rows[n] for n in names];v=[x['gpu_median'] for x in rr];summary[w]={'medians_A_B_B_A':v,'A_mean':(v[0]+v[3])/2,'B_mean':(v[1]+v[2])/2,'speed_ratio':(v[0]+v[3])/(v[1]+v[2]),'quality':rr[1]['vs_Phase19'],'gold':rr[1]['vs_F32gold'],'baseline_gold':rr[1]['Phase19_vs_F32gold'],'LMem0':all(x['LMem0'] for x in rr),'quality_gate':rr[1]['vs_Phase19']['PSNR_peak1']>50 and rr[1]['vs_F32gold']['PSNR_peak1']>=rr[1]['Phase19_vs_F32gold']['PSNR_peak1']}
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');lines=['# Phase20 single joint candidate,50/80 ABBA','','PSNR peak1 on visible encoded RGB. Mean run medians are only a summary;all raw grouped stats stay in results.json/logs.','', '| Width | A1 | B1 | B2 | A2 | Speed ratio | PSNR vsP19 | maxabs vsP19 | P19→candidate PSNR vsF32 | LOCAL0 |','|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
for w,x in summary.items():lines.append(f'| {w} | '+' | '.join(f'{t:.3f}' for t in x['medians_A_B_B_A'])+f' | {x["speed_ratio"]:.4f}× | {x["quality"]["PSNR_peak1"]:.6f} | {x["quality"]["maxabs"]:.9f} | {x["baseline_gold"]["PSNR_peak1"]:.6f}→{x["gold"]["PSNR_peak1"]:.6f} | {x["LMem0"]} |')
lines+=['','## C32/Wave2 profile totals (independent instrumented frame)','','| Run | Width | Kernel | ms | REG | LOCAL | Shared | OccW |','|---|---:|---|---:|---:|---:|---:|---:|']
for n,x in rows.items():
 if n.startswith('candidate-quick'):continue
 for k,v in x['kernels'].items():
  if k.startswith(('c32_wave1','c64_wave2','c128_wave2','c256_wave2')):lines.append(f'| {n} | {x["width"]} | {k} | {v["ms"]:.6f} | {int(v["regs"])} | {int(v["lmem"])} | {int(v["smem"])} | {int(v["occw"])} |')
(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:10]))

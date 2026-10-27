from pathlib import Path
import json,statistics as st
p=Path(__file__).resolve().parent;rows=json.loads((p/'bench.json').read_text());assert len(rows)==30;result={};lines=['# V2.6 Low/High — matched frame timing and output distances','','Preset2 / Style1, 50 warmup / 80 iter, forward ABBA and reverse BAAB. Timing values are means of per-process GPU medians/minima, not pooled frame medians. Default DVFS. V1 reference runs are for quality and determinism, not a paired speed comparison.','','| Width | V2.4 median ms | Low/High median ms | V2.4 min ms | Low/High min ms | Time decrease | Forward / reverse |','|---:|---:|---:|---:|---:|---:|---:|']
for w in [1280,1600,1920]:
 a=[x for x in rows if x['width']==w and x['variant']=='baseline'];b=[x for x in rows if x['width']==w and x['variant']=='lowhigh'];mean=lambda r,k:st.mean(x['metrics'][k] for x in r);am,bm=mean(a,'gpu_median_ms'),mean(b,'gpu_median_ms');dirs={}
 for d in ['forward','reverse']:
  aa=[x for x in a if d in x['name']];bb=[x for x in b if d in x['name']];dirs[d]={'baseline_median_ms':mean(aa,'gpu_median_ms'),'candidate_median_ms':mean(bb,'gpu_median_ms'),'gain_percent':100*(1-mean(bb,'gpu_median_ms')/mean(aa,'gpu_median_ms'))}
 assert all(d['gain_percent']>0 for d in dirs.values());assert len({x['quality']['sha256'] for x in b})==1
 quality=b[0]['quality'];assert all(q['psnr_db']>=58 for q in quality['vs'].values());assert all(x['metrics']['nonfinite']==0 for x in b);assert w!=1280 or all(x['quality']['sky_sign_changes']==0 for x in b)
 result[str(w)]={'baseline_median_ms':am,'candidate_median_ms':bm,'baseline_min_ms':mean(a,'gpu_min_ms'),'candidate_min_ms':mean(b,'gpu_min_ms'),'gain_percent':100*(1-bm/am),'directions':dirs,'quality':quality,'runs_per_version':4};r=result[str(w)];lines.append(f'| {w} | {am:.5f} | {bm:.5f} | {r["baseline_min_ms"]:.5f} | {r["candidate_min_ms"]:.5f} | {r["gain_percent"]:.3f}% | {dirs["forward"]["gain_percent"]:.3f}% / {dirs["reverse"]["gain_percent"]:.3f}% |')
lines+=['','PSNR peak=1 in final bench RGB. These are distances to ported reference implementations, not native sm120 or FP32 full-network gold. Different K partitions change FP16 rounding; outputs are not bit identical across versions.','','| Width | vs V2.4 PSNR | vs V2.4 maxabs | vs V1 PSNR | vs V1 maxabs | Sky sign changes / HF RMS |','|---:|---:|---:|---:|---:|---|']
for w,r in result.items():
 q=r['quality'];a=q['vs']['baseline'];b=q['vs']['v1'];sky=f'{q["sky_sign_changes"]} / {q["sky_hf_rms"]:.12f}' if 'sky_sign_changes' in q else '—';lines.append(f'| {w} | {a["psnr_db"]:.6f} dB | {a["maxabs"]:.9f} | {b["psnr_db"]:.6f} dB | {b["maxabs"]:.9f} | {sky} |')
(p/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

from pathlib import Path
import json
p=Path(__file__).resolve().parent;d=json.loads((p/'results.json').read_text());lines=['# Phase14 final native-Host validation','','Small31/Style1, Graph off,50warmup/80iter, defaultDVFS140W cap. Each row is one run; PROFILE_TOTAL is a separate instrumented frame. No cross-run minima combined.','', '| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for order,sel,ref in [('Forward','default400','baseline-confirm'),('Reverse','default400-reverse','baseline-confirm-reverse')]:
 for w,tier in [('1280','720p1280x768'),('1600','900p1600x1024'),('1920','1080p1920x1152')]:
  baseline=('control256-final' if order=='Forward' else 'control256-final-reverse') if w=='1280' else ref
  seq=[baseline,sel] if order=='Forward' else [sel,baseline]
  for v in seq:
   c=d[v][w];t=c['telemetry'];lines.append(f'| {order} | {tier} | {v} | {c["gpu_min"]:.3f} | {c["gpu_median"]:.3f} | {c["wall_median"]:.3f} | {c["profile_total"]:.6f} | {t["sm_mhz"]} | {t["power_w"]:.2f} | {t["temp_c"]} |')
lines+=['','720 controls use the corrected256 path;900/1080 controls use immutable Phase12 modules. Native final default400 has no forced bucket env. Both720 paths are equal;400 gains only0.035/0.043ms in these final pairs. Earlier flat/negative controls andABBA retained in results.md. Do not claim a large end-to-end speedup.900/1080 variations are not asserted as gains/regressions from unchanged math.','', '| Tier | Visible PSNR vs trustedF32 | Maxabs | Invalid | Diff vs oldPhase12 |','|---|---:|---:|---:|---:|']
for w,t in [('1280','720p'),('1600','900p'),('1920','1080p')]:
 c=d['default400'][w];q=c['visible_vs_trusted_F32'];lines.append(f'| {t} | {q["psnr_peak1"]:.12f} | {q["maxabs"]:.12f} | {c["invalid"]} | {c["vs_phase12_old"]["bitdiff"]} |')
lines+=['','Two rounds: first/last0bit,32/32LOCAL0, all outputs equal the corrected baseline.720 old-output changes are authorized correctness changes. The new720 gold is recorded in gold-manifest.json.','', 'Full32-kernel table and every control: [results.md](results.md). CPU/layout/NaN policy: [correctness.md](correctness.md).']
(p/'final-results.md').write_text('\n'.join(lines)+'\n')

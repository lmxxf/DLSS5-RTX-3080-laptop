from pathlib import Path
import json
p=Path(__file__).resolve().parent;d=json.loads((p/'results.json').read_text())
lines=['# Phase12 final paired results','','All times ms. Small31/Style1, Graph off, 50 warmup/80 iter, default DVFS. Each row is one run, PROFILE_TOTAL is a separate instrumented frame.','', '| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for order,variants in [('Forward',['baseline-final','selected']),('Reverse',['selected-reverse','baseline-final-reverse'])]:
 for w,tier in [('1280','720p 1280x768'),('1600','900p 1600x1024'),('1920','1080p 1920x1152')]:
  for v in variants:
   c=d[v][w];t=c['telemetry'];lines.append(f'| {order} | {tier} | {v} | {c["gpu_min"]:.3f} | {c["gpu_median"]:.3f} | {c["wall_median"]:.3f} | {c["kernel_total"]:.6f} | {t["sm_mhz"]} | {t["power_w"]:.2f} | {t["temp_c"]} |')
lines+=['','The final forward 1080p pair is effectively flat (0.002 ms). Reverse improves 0.368 ms. Supplemental ABBA confirms the same direction, with varying magnitude; do not claim a fixed speedup. 720p is flat/slightly negative. 900p changes sign across final pairs, hence no stable gain claim.','', '| ABBA | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med |','|---|---:|---:|---:|---:|---:|---:|']
for v in ['baseline-final-abba-a','final-abba-b1','final-abba-b2','baseline-final-abba-a2']:
 c=d[v]['1920'];t=c['telemetry'];lines.append(f'| {v} | {c["gpu_min"]:.3f} | {c["gpu_median"]:.3f} | {c["wall_median"]:.3f} | {c["kernel_total"]:.6f} | {t["sm_mhz"]} | {t["power_w"]:.2f} |')
lines+=['','All candidate outputs in all rounds are equal to Phase11 (including supplementary runs). All six final tier-runs: invalid0, first/last bitdiff0, 32/32 LOCAL0. F32 visible PSNR900=46.975322410562406 dB,1080=46.100947087035124 dB, unchanged. 720 has no accepted absolute F32 reference; see f32-reference-status.json.','', '32-kernel tables and all per-station controls are in [results.md](results.md). Source-build and actual CUDA load40/40/1918 are independently recorded.']
(p/'final-results.md').write_text('\n'.join(lines)+'\n')

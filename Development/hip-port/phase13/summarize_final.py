from pathlib import Path
import json
p=Path(__file__).resolve().parent;d=json.loads((p/'results.json').read_text())
lines=['# Phase13 final paired results','','All times ms. Small31/Style1, Graph off, 50 warmup/80 iter, default DVFS. Each row is one run, PROFILE_TOTAL is a separate instrumented frame.','', '| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for order,variants in [('Forward',['baseline-final','selected']),('Reverse',['selected-reverse','baseline-final-reverse'])]:
 for w,tier in [('1280','720p 1280x768'),('1600','900p 1600x1024'),('1920','1080p 1920x1152')]:
  for v in variants:
   c=d[v][w];t=c['telemetry'];lines.append(f'| {order} | {tier} | {v} | {c["gpu_min"]:.3f} | {c["gpu_median"]:.3f} | {c["wall_median"]:.3f} | {c["kernel_total"]:.6f} | {t["sm_mhz"]} | {t["power_w"]:.2f} | {t["temp_c"]} |')
lines+=['','No performance change retained. All40 final cubin hashes equal Phase12. Differences above are independent-run variation of identical binaries, not a Phase13 speedup.','', 'All six final tier-runs: full output bitdiff0 vsPhase12, invalid0, first/last bitdiff0,32/32 LOCAL0. Trusted F32 visible PSNR900=46.975322410562406dB,1080=46.100947087035124dB unchanged. No default720 absoluteF32PSNR; see reference-audit.md.','', 'All controls and32-kernel tables: [results.md](results.md).']
(p/'final-results.md').write_text('\n'.join(lines)+'\n')

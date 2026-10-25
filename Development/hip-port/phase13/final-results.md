# Phase13 final paired results

All times ms. Small31/Style1, Graph off, 50 warmup/80 iter, default DVFS. Each row is one run, PROFILE_TOTAL is a separate instrumented frame.

| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Forward | 720p 1280x768 | baseline-final | 13.869 | 14.048 | 14.149 | 13.521920 | 1612.5 | 125.37 | 62.5 |
| Forward | 720p 1280x768 | selected | 13.975 | 14.123 | 14.198 | 13.440000 | 1635.0 | 139.71 | 65.0 |
| Forward | 900p 1600x1024 | baseline-final | 23.204 | 23.569 | 23.670 | 21.661696 | 1575.0 | 139.78 | 67.0 |
| Forward | 900p 1600x1024 | selected | 23.205 | 23.646 | 23.763 | 21.706752 | 1560.0 | 139.83 | 69.5 |
| Forward | 1080p 1920x1152 | baseline-final | 31.169 | 31.619 | 31.731 | 29.149183 | 1545.0 | 139.30 | 72.0 |
| Forward | 1080p 1920x1152 | selected | 31.264 | 31.835 | 31.934 | 28.743680 | 1537.5 | 139.28 | 73.0 |
| Reverse | 720p 1280x768 | selected-reverse | 14.230 | 14.377 | 14.472 | 13.700096 | 1605.0 | 139.73 | 74.0 |
| Reverse | 720p 1280x768 | baseline-final-reverse | 14.225 | 14.410 | 14.483 | 13.628384 | 1605.0 | 139.67 | 75.0 |
| Reverse | 900p 1600x1024 | selected-reverse | 23.397 | 23.932 | 24.067 | 21.781504 | 1560.0 | 138.84 | 75.5 |
| Reverse | 900p 1600x1024 | baseline-final-reverse | 23.682 | 23.933 | 24.035 | 21.772288 | 1560.0 | 139.73 | 76.0 |
| Reverse | 1080p 1920x1152 | selected-reverse | 31.537 | 32.057 | 32.188 | 29.387775 | 1537.5 | 139.59 | 77.0 |
| Reverse | 1080p 1920x1152 | baseline-final-reverse | 31.528 | 32.109 | 32.208 | 28.978176 | 1522.5 | 139.55 | 78.0 |

No performance change retained. All40 final cubin hashes equal Phase12. Differences above are independent-run variation of identical binaries, not a Phase13 speedup.

All six final tier-runs: full output bitdiff0 vsPhase12, invalid0, first/last bitdiff0,32/32 LOCAL0. Trusted F32 visible PSNR900=46.975322410562406dB,1080=46.100947087035124dB unchanged. No default720 absoluteF32PSNR; see reference-audit.md.

All controls and32-kernel tables: [results.md](results.md).

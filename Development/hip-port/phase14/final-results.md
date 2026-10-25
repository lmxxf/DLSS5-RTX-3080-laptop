# Phase14 final native-Host validation

Small31/Style1, Graph off,50warmup/80iter, defaultDVFS140W cap. Each row is one run; PROFILE_TOTAL is a separate instrumented frame. No cross-run minima combined.

| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Forward | 720p1280x768 | control256-final | 14.006 | 14.182 | 14.264 | 13.627392 | 1605.0 | 134.20 | 65.0 |
| Forward | 720p1280x768 | default400 | 14.076 | 14.147 | 14.245 | 13.498368 | 1620.0 | 139.66 | 67.0 |
| Forward | 900p1600x1024 | baseline-confirm | 23.239 | 23.640 | 23.722 | 21.630976 | 1590.0 | 139.53 | 69.0 |
| Forward | 900p1600x1024 | default400 | 23.375 | 23.722 | 23.882 | 22.387712 | 1575.0 | 139.79 | 71.0 |
| Forward | 1080p1920x1152 | baseline-confirm | 31.287 | 31.681 | 31.836 | 28.406816 | 1537.5 | 139.82 | 73.0 |
| Forward | 1080p1920x1152 | default400 | 31.347 | 31.826 | 31.926 | 28.646400 | 1545.0 | 139.69 | 75.0 |
| Reverse | 720p1280x768 | default400-reverse | 14.204 | 14.381 | 14.468 | 13.714240 | 1590.0 | 139.69 | 75.0 |
| Reverse | 720p1280x768 | control256-final-reverse | 14.368 | 14.424 | 14.517 | 13.995008 | 1590.0 | 139.63 | 75.0 |
| Reverse | 900p1600x1024 | default400-reverse | 23.586 | 23.885 | 23.996 | 21.772288 | 1560.0 | 139.28 | 76.0 |
| Reverse | 900p1600x1024 | baseline-confirm-reverse | 23.799 | 23.998 | 24.072 | 21.764096 | 1552.5 | 139.86 | 76.5 |
| Reverse | 1080p1920x1152 | default400-reverse | 31.250 | 32.111 | 32.206 | 28.637216 | 1530.0 | 139.69 | 78.0 |
| Reverse | 1080p1920x1152 | baseline-confirm-reverse | 31.524 | 32.100 | 32.225 | 28.738560 | 1530.0 | 139.69 | 79.0 |

720 controls use the corrected256 path;900/1080 controls use immutable Phase12 modules. Native final default400 has no forced bucket env. Both720 paths are equal;400 gains only0.035/0.043ms in these final pairs. Earlier flat/negative controls andABBA retained in results.md. Do not claim a large end-to-end speedup.900/1080 variations are not asserted as gains/regressions from unchanged math.

| Tier | Visible PSNR vs trustedF32 | Maxabs | Invalid | Diff vs oldPhase12 |
|---|---:|---:|---:|---:|
| 720p | 43.577947912339 | 0.050935506821 | 0 | 2947224 |
| 900p | 46.975322410562 | 0.040045499802 | 0 | 0 |
| 1080p | 46.100947087035 | 0.041602730751 | 0 | 0 |

Two rounds: first/last0bit,32/32LOCAL0, all outputs equal the corrected baseline.720 old-output changes are authorized correctness changes. The new720 gold is recorded in gold-manifest.json.

Full32-kernel table and every control: [results.md](results.md). CPU/layout/NaN policy: [correctness.md](correctness.md).

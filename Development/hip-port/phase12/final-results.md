# Phase12 final paired results

All times ms. Small31/Style1, Graph off, 50 warmup/80 iter, default DVFS. Each row is one run, PROFILE_TOTAL is a separate instrumented frame.

| Order | Tier | Variant | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med | Temp C med |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Forward | 720p 1280x768 | baseline-final | 14.012 | 14.555 | 14.652 | 14.083072 | 1635.0 | 128.16 | 67.0 |
| Forward | 720p 1280x768 | selected | 13.884 | 14.588 | 14.730 | 13.984768 | 1612.5 | 137.11 | 69.0 |
| Forward | 900p 1600x1024 | baseline-final | 23.261 | 24.159 | 24.277 | 22.281216 | 1575.0 | 139.16 | 71.0 |
| Forward | 900p 1600x1024 | selected | 23.244 | 24.236 | 24.339 | 22.022144 | 1575.0 | 139.26 | 73.0 |
| Forward | 1080p 1920x1152 | baseline-final | 31.591 | 32.639 | 32.736 | 29.413376 | 1552.5 | 139.30 | 74.0 |
| Forward | 1080p 1920x1152 | selected | 31.327 | 32.637 | 32.754 | 28.468224 | 1537.5 | 139.50 | 76.0 |
| Reverse | 720p 1280x768 | selected-reverse | 14.233 | 14.884 | 14.973 | 14.102528 | 1590.0 | 138.98 | 76.0 |
| Reverse | 720p 1280x768 | baseline-final-reverse | 14.232 | 14.876 | 14.975 | 14.936096 | 1590.0 | 139.35 | 77.0 |
| Reverse | 900p 1600x1024 | selected-reverse | 23.465 | 24.569 | 24.691 | 23.024640 | 1567.5 | 139.77 | 77.0 |
| Reverse | 900p 1600x1024 | baseline-final-reverse | 23.638 | 24.644 | 24.778 | 23.185408 | 1567.5 | 139.69 | 77.5 |
| Reverse | 1080p 1920x1152 | selected-reverse | 31.583 | 32.849 | 32.998 | 30.803968 | 1530.0 | 139.37 | 79.0 |
| Reverse | 1080p 1920x1152 | baseline-final-reverse | 32.268 | 33.217 | 33.317 | 30.488576 | 1530.0 | 139.36 | 80.0 |

The final forward 1080p pair is effectively flat (0.002 ms). Reverse improves 0.368 ms. Supplemental ABBA confirms the same direction, with varying magnitude; do not claim a fixed speedup. 720p is flat/slightly negative. 900p changes sign across final pairs, hence no stable gain claim.

| ABBA | GPU min | GPU median | Wall median | PROFILE_TOTAL | SM MHz med | Power W med |
|---|---:|---:|---:|---:|---:|---:|
| baseline-final-abba-a | 31.322 | 31.966 | 32.130 | 28.655552 | 1545.0 | 139.72 |
| final-abba-b1 | 30.949 | 31.921 | 32.048 | 33.126400 | 1530.0 | 139.50 |
| final-abba-b2 | 31.629 | 32.887 | 33.103 | 30.225408 | 1537.5 | 139.49 |
| baseline-final-abba-a2 | 31.631 | 33.221 | 33.341 | 31.383552 | 1545.0 | 139.61 |

All candidate outputs in all rounds are equal to Phase11 (including supplementary runs). All six final tier-runs: invalid0, first/last bitdiff0, 32/32 LOCAL0. F32 visible PSNR900=46.975322410562406 dB,1080=46.100947087035124 dB, unchanged. 720 has no accepted absolute F32 reference; see f32-reference-status.json.

32-kernel tables and all per-station controls are in [results.md](results.md). Source-build and actual CUDA load40/40/1918 are independently recorded.

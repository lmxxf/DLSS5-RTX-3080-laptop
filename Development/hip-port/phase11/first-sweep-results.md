# Phase11 controls

50 warmup/80 iterations, Graph off; separate instrumented frame. Default DVFS, not clock locked.

| Variant | Width | GPU min /median | Wall median | Kernel total | LMem kinds | SM MHz med | Power W med |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline-a | 1280 | 13.825 /14.395 | 14.482 | 13.383680 | 0 | 1635.0 | 131.96 |
| baseline-a | 1600 | 22.957 /23.805 | 23.910 | 21.660672 | 0 | 1605.0 | 139.23000000000002 |
| baseline-a | 1920 | 31.067 /32.542 | 32.668 | 28.832768 | 0 | 1567.5 | 139.36 |
| half-store | 1280 | 14.046 /14.349 | 14.522 | 13.460512 | 0 | 1620.0 | 139.25 |
| half-store | 1600 | 23.110 /24.253 | 24.366 | 23.124992 | 0 | 1575.0 | 139.55 |
| half-store | 1920 | 31.122 /31.953 | 32.064 | 28.459008 | 0 | 1552.5 | 139.25 |

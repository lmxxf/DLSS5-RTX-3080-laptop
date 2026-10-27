# V2.5 Hybrid controls — negative result

50 warmup / 80 iterations, forward ABBA and reverse BAAB. Means of per-process GPU medians/minima; default DVFS, no clocks locked. Every output is compared against same-configuration V2.4.

| Scope | Width | V2.4 median ms | Candidate median ms | V2.4 min ms | Candidate min ms | Time decrease | Forward / reverse |
|---|---:|---:|---:|---:|---:|---:|---:|
| all_FB | 1280 | 6.17950 | 6.20500 | 6.03100 | 6.07350 | -0.413% | -0.764% / -0.072% |
| all_FB | 1600 | 8.93025 | 9.04750 | 8.76150 | 8.78400 | -1.313% | -0.598% / -2.016% |
| all_FB | 1920 | 11.72275 | 11.96775 | 11.46250 | 11.47400 | -2.090% | -2.243% / -1.938% |
| FB00_only | 1280 | 6.16425 | 6.15150 | 6.08175 | 6.05075 | 0.207% | 0.376% / 0.040% |
| FB00_only | 1920 | 11.70750 | 11.70525 | 11.52050 | 11.56550 | 0.019% | -0.193% / 0.230% |

# Phase 10 三档完整对照

| 档位（CUDA处理尺寸） | CUDA GPU min | CUDA GPU median | CUDA Wall median | CUDA PROFILE_TOTAL | invalid | PTX历史GPU median |
|---|---:|---:|---:|---:|---:|---:|
| 720p（1280×768） | 13.843 | **14.103** | 14.182 | 14.001120 | 0 | 15.83 |
| 900p（1600×1024） | 23.461 | **23.750** | 23.850 | 21.753888 | 0 | 24.47 |
| 1080p（1920×1152） | 30.944 | **31.631** | 31.712 | 28.430336 | 0 | 32.04 |

单位ms，Small31/Style1、Graph off、50 warmup/80 iter。720p本次补测，900p/1080p沿用上一轮最终selected独立复测，不混入其它轮次最小值。PROFILE_TOTAL为独立插桩帧。PTX列为历史标尺，本轮没有统一输入/处理尺寸重跑DLL。

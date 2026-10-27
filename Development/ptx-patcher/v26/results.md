# V2.6 Low/High — matched frame timing and output distances

Preset2 / Style1, 50 warmup / 80 iter, forward ABBA and reverse BAAB. Timing values are means of per-process GPU medians/minima, not pooled frame medians. Default DVFS. V1 reference runs are for quality and determinism, not a paired speed comparison.

| Width | V2.4 median ms | Low/High median ms | V2.4 min ms | Low/High min ms | Time decrease | Forward / reverse |
|---:|---:|---:|---:|---:|---:|---:|
| 1280 | 6.09950 | 5.98000 | 6.02800 | 5.91325 | 1.959% | 2.152% / 1.770% |
| 1600 | 8.92475 | 8.72200 | 8.71250 | 8.52300 | 2.272% | 2.048% / 2.492% |
| 1920 | 11.73225 | 11.46250 | 11.49050 | 11.22550 | 2.299% | 1.894% / 2.701% |

PSNR peak=1 in final bench RGB. These are distances to ported reference implementations, not native sm120 or FP32 full-network gold. Different K partitions change FP16 rounding; outputs are not bit identical across versions.

| Width | vs V2.4 PSNR | vs V2.4 maxabs | vs V1 PSNR | vs V1 maxabs | Sky sign changes / HF RMS |
|---:|---:|---:|---:|---:|---|
| 1280 | 61.819121 dB | 0.004882812 | 62.124349 dB | 0.004394531 | 0 / 0.000102746766 |
| 1600 | 61.767286 dB | 0.005615234 | 61.854969 dB | 0.006103516 | — |
| 1920 | 58.421047 dB | 0.009765625 | 60.884550 dB | 0.007324219 | — |

# V2.2 single-factor and combined controls

RTX 3080 Laptop, default DVFS; each process 50 warmup / 80 iterations. Each tier and factor has forward ABBA and reverse BAAB (four runs per version). Values below are means of per-process GPU medians/minima, not pooled frame medians. peak=1 RGB exact comparison uses the same 50/80 baseline output.

| Factor | Size | V2.1 median ms | Candidate median ms | V2.1 min ms | Candidate min ms | Speed ratio | Forward / reverse gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| async | 1280 | 6.7107 | 6.7432 | 6.6078 | 6.6262 | 0.9952x | -0.69% / -0.29% |
| async | 1600 | 9.7530 | 9.6917 | 9.5968 | 9.5170 | 1.0063x | 0.91% / 0.35% |
| async | 1920 | 12.7513 | 12.6055 | 12.5895 | 12.4160 | 1.0116x | 1.20% / 1.08% |
| swar | 1280 | 6.7500 | 6.2680 | 6.6670 | 6.1790 | 1.0769x | 6.81% / 7.46% |
| swar | 1600 | 9.7560 | 9.1910 | 9.6455 | 9.0163 | 1.0615x | 5.97% / 5.61% |
| swar | 1920 | 12.7725 | 12.0013 | 12.5602 | 11.7698 | 1.0643x | 6.16% / 5.92% |
| combo | 1280 | 6.7390 | 6.2485 | 6.6528 | 6.1327 | 1.0785x | 7.42% / 7.14% |
| combo | 1600 | 9.7835 | 9.1223 | 9.6340 | 8.9475 | 1.0725x | 6.87% / 6.65% |
| combo | 1920 | 12.7797 | 11.8595 | 12.6203 | 11.6993 | 1.0776x | 7.42% / 6.98% |

All exports, static SASS counts (not only dynamically active kernels):

| FB | V2.1 STACK / LDL+STL | Async | SWAR | Combo |
|---|---:|---:|---:|---:|
| 00 | 0 B / 0 | 0 B / 0 | 0 B / 0 | 0 B / 0 |
| 01 | 120 B / 315 | 120 B / 315 | 168 B / 462 | 168 B / 462 |
| 02 | 0 B / 0 | 0 B / 0 | 8 B / 2 | 8 B / 2 |
| 03 | 0 B / 0 | 0 B / 0 | 0 B / 0 | 0 B / 0 |
| 04 | 80 B / 118 | 80 B / 118 | 80 B / 118 | 80 B / 118 |
| 05 | 8 B / 12 | 16 B / 18 | 8 B / 12 | 16 B / 18 |
| 06 | 0 B / 0 | 0 B / 0 | 0 B / 0 | 0 B / 0 |

Do not claim zero-stack: O4 spilling increases in FB01/02/05 despite fewer PTX temporaries. FB04 remains 80 B. Async replaces 316 immediate completion pairs with balanced native mbarrier arrivals; four pre-existing non-bulk groups in FB04 remain unchanged.

A preliminary harness compared baseline 1/1 against baseline 50/80 and detected temporal-frame differences (61.786 dB at 720p). These configurations are now separate golds; this is not a candidate mismatch. All 72 timing runs compare against 50/80 gold and are bit identical.

Telemetry starts during forward 720p, after the earliest timed processes; no fixed clocks or power locks were applied. Raw process order and min/median/wall results are in bench.json.

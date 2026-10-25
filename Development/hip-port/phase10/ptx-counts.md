# Phase 10 static PTX per entry

Counts are static PTX, not executed SASS. Saturation moved into the converter can increase min count when a wrapper already had no outer clamp.

| Kernel | min | max | setp | selp | bra | mma | shfl |
|---|---:|---:|---:|---:|---:|---:|---:|
| c32_wave1_prefix_b8d_w16 | 288→288 | 290→66 | 693→245 | 1112→664 | 18→18 | 84→84 | 209→209 |
| c32_wave1_mapped_b8_w16 | 224→224 | 226→66 | 515→195 | 686→366 | 442→442 | 80→80 | 180→180 |
| c32_wave1_up_b8_w16 | 224→224 | 226→66 | 512→192 | 942→622 | 7→7 | 84→84 | 224→224 |
| c64_wave2_bi_bo_w16 | 64→256 | 66→66 | 621→237 | 963→579 | 19→19 | 100→100 | 184→184 |
| c128_wave2_bi_bo_w16 | 64→256 | 66→66 | 623→239 | 963→579 | 19→19 | 100→100 | 184→184 |
| c256_wave2_bi_bo_w16 | 64→256 | 66→66 | 627→243 | 963→579 | 22→22 | 100→100 | 184→184 |
| c512_qkv_attention_compact_w16 | 176→320 | 180→180 | 446→158 | 932→644 | 11→11 | 80→80 | 292→292 |

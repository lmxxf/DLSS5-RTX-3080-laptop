# Static PTX instructions per entry

These are static PTX counts, not executed instruction counts or final SASS. Hoist uses step12 for unchanged non-C32 modules.

| Kernel | Variant | bra | min | max | mma | Lines |
|---|---|---:|---:|---:|---:|---:|
| c32_wave1_prefix_b8d_w16 | baseline | 617 | 528 | 530 | 84 | 14107 |
| c32_wave1_prefix_b8d_w16 | step12 | 10 | 288 | 290 | 84 | 13528 |
| c32_wave1_prefix_b8d_w16 | hoist | 10 | 288 | 290 | 84 | 13528 |
| c32_wave1_mapped_b8_w16 | baseline | 442 | 400 | 402 | 80 | 11104 |
| c32_wave1_mapped_b8_w16 | step12 | 18 | 224 | 226 | 80 | 10580 |
| c32_wave1_mapped_b8_w16 | hoist | 18 | 224 | 226 | 80 | 10580 |
| c64_wave2_bi_bo_w16 | baseline | 540 | 128 | 130 | 100 | 12869 |
| c64_wave2_bi_bo_w16 | step12 | 19 | 64 | 66 | 100 | 12519 |
| c64_wave2_bi_bo_w16 | hoist | 19 | 64 | 66 | 100 | 12519 |
| c128_wave2_bi_bo_w16 | baseline | 540 | 128 | 130 | 100 | 12863 |
| c128_wave2_bi_bo_w16 | step12 | 19 | 64 | 66 | 100 | 12513 |
| c128_wave2_bi_bo_w16 | hoist | 19 | 64 | 66 | 100 | 12513 |
| c256_wave2_bi_bo_w16 | baseline | 544 | 128 | 130 | 100 | 13100 |
| c256_wave2_bi_bo_w16 | step12 | 22 | 64 | 66 | 100 | 12769 |
| c256_wave2_bi_bo_w16 | hoist | 22 | 64 | 66 | 100 | 12769 |

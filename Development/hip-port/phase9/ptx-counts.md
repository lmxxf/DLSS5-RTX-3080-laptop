# Phase 9 static PTX per entry

Counts include loops statically; do not treat them as dynamic instructions or SASS.

| Kernel | Variant | shfl | selp | prmt | bra | mma |
|---|---|---:|---:|---:|---:|---:|
| c32_wave1_prefix_b8d_w16 | phase8 | 229 | 1136 | 332 | 10 | 84 |
| c32_wave1_prefix_b8d_w16 | v-bridge | 209 | 1100 | 328 | 10 | 84 |
| c32_wave1_prefix_b8d_w16 | selected | 209 | 1112 | 328 | 18 | 84 |
| c32_wave1_mapped_b8_w16 | phase8 | 200 | 870 | 324 | 10 | 80 |
| c32_wave1_mapped_b8_w16 | v-bridge | 180 | 834 | 320 | 10 | 80 |
| c32_wave1_mapped_b8_w16 | selected | 180 | 686 | 320 | 442 | 80 |
| c32_wave1_finish_b8_w16 | phase8 | 184 | 993 | 340 | 37 | 92 |
| c32_wave1_finish_b8_w16 | v-bridge | 164 | 957 | 336 | 37 | 92 |
| c32_wave1_finish_b8_w16 | selected | 164 | 957 | 336 | 37 | 92 |
| c64_wave2_bi_bo_w16 | phase8 | 204 | 999 | 384 | 19 | 100 |
| c64_wave2_bi_bo_w16 | v-bridge | 184 | 963 | 380 | 19 | 100 |
| c64_wave2_bi_bo_w16 | selected | 184 | 963 | 380 | 19 | 100 |
| c128_wave2_bi_bo_w16 | phase8 | 204 | 999 | 384 | 19 | 100 |
| c128_wave2_bi_bo_w16 | v-bridge | 184 | 963 | 380 | 19 | 100 |
| c128_wave2_bi_bo_w16 | selected | 184 | 963 | 380 | 19 | 100 |
| c256_wave2_bi_bo_w16 | phase8 | 204 | 999 | 404 | 22 | 100 |
| c256_wave2_bi_bo_w16 | v-bridge | 184 | 963 | 400 | 22 | 100 |
| c256_wave2_bi_bo_w16 | selected | 184 | 963 | 400 | 22 | 100 |

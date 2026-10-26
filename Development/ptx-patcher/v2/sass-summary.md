# Static SASS / resources (all exports, not dynamic executed counts)

| FB | old SHFL total | new SHFL total | old max STACK | new max STACK |
|---|---:|---:|---:|---:|
| 00 | 26300 | 1274 | 264 | 240 |
| 01 | 16627 | 706 | 80 | 120 |
| 02 | 14195 | 706 | 8 | 0 |
| 03 | 12371 | 706 | 232 | 200 |
| 04 | 6563 | 610 | 1152 | 1032 |
| 05 | 4963 | 258 | 608 | 480 |
| 06 | 834 | 257 | 456 | 168 |

Original reduction SHFLs remain. Zero-SHFL refers only to the replacement MMA operand preparation. STACK is compiler-reported stack; LOCAL may be0 while stack spill loads/stores exist. Includes unexecuted variants.

## Representative matching FP8 exports

| FB | Kernel | old/new SHFL | old/new REG | old/new STACK |
|---|---|---:|---:|---:|
| 0 | cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8 | 1399/80 | 168/168 | 200/48 |
| 0 | cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8 | 1344/48 | 168/168 | 152/200 |
| 1 | cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8 | 1112/80 | 167/168 | 0/24 |
| 1 | cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8 | 1424/48 | 168/168 | 56/48 |
| 2 | cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8 | 1208/80 | 168/168 | 0/0 |
| 2 | cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8 | 1152/48 | 168/168 | 0/0 |
| 3 | cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8 | 1064/80 | 128/128 | 232/168 |
| 3 | cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8 | 1008/48 | 128/128 | 208/200 |
| 4 | cc_split_swin_16h_final_head_512_wait_fp8 | 96/0 | 168/168 | 360/24 |
| 4 | cc_split_swin_16h_final_head_512_fp8 | 96/0 | 168/168 | 352/32 |
| 5 | cc_vit_1d_projection_chained_fp8 | 128/0 | 168/154 | 264/0 |
| 5 | cc_vit_1d_projection_wait_fp8 | 128/0 | 168/154 | 256/0 |
| 6 | cc_dec_input_upsample_1024_512_tilesync_fp8 | 416/128 | 168/168 | 456/160 |
| 6 | cc_dec_input_upsample_1024_512_fp8 | 416/128 | 168/168 | 456/168 |

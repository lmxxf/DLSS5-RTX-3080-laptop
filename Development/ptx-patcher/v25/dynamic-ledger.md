# Loop-corrected workload ledger

HMMA and MMA-decoder PTX events below are measured by an independent instrumented V2.4 DLL (one lane per converged MMA warp), with exact RGB agreement. Loop headers are measured directly. SASS auxiliary totals are a compute-loop-expanded model, not a hardware dynamic instruction counter. The model assumes one pass through non-MMA loops and unions conditional blocks; spin retries and actual predication/divergence are not measured. Instrumented timings are never used for speed claims.

| Width | FB | Measured HMMA warp instructions | Decoder PRMT PTX events | Loop-expanded auxiliary SASS model | TC floor ms at assumed clock |
|---:|---:|---:|---:|---:|---:|
| 1280 | 0 | 25,696,224 | 40,276,264 | not modeled | 1.263335 |
| 1280 | 4 | 4,694,016 | 5,265,408 | 33309600 | 0.230778 |
| 1280 | 5 | 20,185,088 | 19,726,336 | 162130944 | 0.992384 |
| 1600 | 0 | 40,691,424 | 63,778,600 | not modeled | 2.112743 |
| 1600 | 4 | 7,155,712 | 8,045,568 | 50889440 | 0.371532 |
| 1600 | 5 | 27,000,832 | 26,411,008 | 216246272 | 1.401912 |
| 1920 | 0 | 54,871,200 | 86,002,696 | not modeled | 2.848972 |
| 1920 | 4 | 9,699,328 | 11,026,432 | 69783168 | 0.503600 |
| 1920 | 5 | 35,389,440 | 35,061,760 | 286136320 | 1.837458 |

## Measured compute-loop trips per launched warp

| Width | Kernel | Loop trips | HMMA / warp |
|---:|---|---|---:|
| 1280 | cc_split_swin_16h_ffwd_512_chained_fp8 | 7, 8 | 1024 |
| 1280 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | 7, 8 | 2048 |
| 1280 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | 8 | 1024 |
| 1280 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | 8 | 1024 |
| 1280 | cc_split_swin_16h_final_head_512_wait_fp8 | 8 | 512 |
| 1280 | cc_split_swin_16h_proj_512_chained_fp8 | 8 | 512 |
| 1280 | cc_split_swin_16h_proj_512_outview_wait_fp8 | 8 | 1024 |
| 1280 | cc_split_swin_16h_proj_pool_512_chained_fp8 | 7 | 1024 |
| 1280 | cc_split_swin_16h_qkv_512_chained_fp8 | 7 | 1664 |
| 1280 | cc_vit_1d_attention_chained_fp8 | 5 | 640 |
| 1280 | cc_vit_1d_ffn_contract_chained_fp8 | 15 | 2048 |
| 1280 | cc_vit_1d_ffn_expand_chained_fp8 | 16 | 2048 |
| 1280 | cc_vit_1d_ffn_expand_publish_fp8 | 16 | 2048 |
| 1280 | cc_vit_1d_projection_chained_fp8 | 7 | 512 |
| 1280 | cc_vit_1d_projection_wait_fp8 | 7 | 512 |
| 1280 | cc_vit_1d_qkv_chained_fp8 | 15 | 1536 |
| 1600 | cc_split_swin_16h_ffwd_512_chained_fp8 | 7, 8 | 1024 |
| 1600 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | 7, 8 | 2048 |
| 1600 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | 8 | 1024 |
| 1600 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | 8 | 1024 |
| 1600 | cc_split_swin_16h_final_head_512_wait_fp8 | 8 | 512 |
| 1600 | cc_split_swin_16h_proj_512_chained_fp8 | 8 | 512 |
| 1600 | cc_split_swin_16h_proj_512_outview_wait_fp8 | 8 | 1024 |
| 1600 | cc_split_swin_16h_proj_pool_512_chained_fp8 | 7 | 1024 |
| 1600 | cc_split_swin_16h_qkv_512_chained_fp8 | 7 | 1664 |
| 1600 | cc_vit_1d_attention_chained_fp8 | 7 | 896 |
| 1600 | cc_vit_1d_ffn_contract_chained_fp8 | 15 | 2048 |
| 1600 | cc_vit_1d_ffn_expand_chained_fp8 | 16 | 2048 |
| 1600 | cc_vit_1d_ffn_expand_publish_fp8 | 16 | 2048 |
| 1600 | cc_vit_1d_projection_chained_fp8 | 7 | 512 |
| 1600 | cc_vit_1d_projection_wait_fp8 | 7 | 512 |
| 1600 | cc_vit_1d_qkv_chained_fp8 | 15 | 1536 |
| 1920 | cc_split_swin_16h_ffwd_512_chained_fp8 | 7, 8 | 1024 |
| 1920 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | 7, 8 | 2048 |
| 1920 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | 8 | 1024 |
| 1920 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | 8 | 1024 |
| 1920 | cc_split_swin_16h_final_head_512_wait_fp8 | 8 | 512 |
| 1920 | cc_split_swin_16h_proj_512_chained_fp8 | 8 | 512 |
| 1920 | cc_split_swin_16h_proj_512_outview_wait_fp8 | 8 | 1024 |
| 1920 | cc_split_swin_16h_proj_pool_512_chained_fp8 | 7 | 1024 |
| 1920 | cc_split_swin_16h_qkv_512_chained_fp8 | 7 | 1664 |
| 1920 | cc_vit_1d_attention_chained_fp8 | 10 | 1280 |
| 1920 | cc_vit_1d_ffn_contract_chained_fp8 | 15 | 2048 |
| 1920 | cc_vit_1d_ffn_expand_chained_fp8 | 16 | 2048 |
| 1920 | cc_vit_1d_ffn_expand_publish_fp8 | 16 | 2048 |
| 1920 | cc_vit_1d_projection_chained_fp8 | 7 | 512 |
| 1920 | cc_vit_1d_projection_wait_fp8 | 7 | 512 |
| 1920 | cc_vit_1d_qkv_chained_fp8 | 15 | 1536 |

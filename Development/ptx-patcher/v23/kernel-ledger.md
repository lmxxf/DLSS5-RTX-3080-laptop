# V2.2 actual NVAPI D3D12 launch ledger

50 warmup / 20 measured frames; D3D12 timestamps bracket each unmodified single-kernel LaunchCuKernelChain call. Native CUDA export hooks observed no launches; NVAPI CreateCuModule/CreateCuFunction resolves names. GPU timestamp intervals include dispatch-local overhead; they are not instruction stall counters.

| Width | FB | Calls/frame | Median aggregate ms |
|---:|---:|---:|---:|
| 1280 | 5 | 42 | 2.000384 |
| 1280 | 0 | 6 | 1.833984 |
| 1280 | 4 | 17 | 0.633344 |
| 1280 | 1 | 4 | 0.537600 |
| 1280 | 3 | 4 | 0.499200 |
| 1280 | 2 | 4 | 0.467968 |
| 1280 | 13 | 1 | 0.056320 |
| 1280 | 14 | 2 | 0.033792 |
| 1280 | 6 | 2 | 0.033792 |
| 1920 | 0 | 6 | 4.059648 |
| 1920 | 5 | 42 | 2.993152 |
| 1920 | 1 | 4 | 1.143808 |
| 1920 | 3 | 4 | 1.111040 |
| 1920 | 2 | 4 | 0.965120 |
| 1920 | 4 | 17 | 0.901632 |
| 1920 | 13 | 1 | 0.125952 |
| 1920 | 14 | 2 | 0.088064 |
| 1920 | 6 | 2 | 0.044032 |

## 1280: all actual launches

| Order | FB | Kernel | Grid | Block | Median ms |
|---:|---:|---|---|---|---:|
| 0 | 14 | cg2r_copy_kernel | [80, 45, 1] | [16, 16, 1] | 0.018432 |
| 1 | 6 | cc_cb_clear | [84, 1, 1] | [256, 1, 1] | 0.002048 |
| 2 | 0 | cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8 | [168, 96, 1] | [32, 1, 1] | 0.609792 |
| 3 | 0 | cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8 | [84, 48, 1] | [32, 1, 1] | 0.145408 |
| 4 | 0 | cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8 | [85, 49, 1] | [32, 1, 1] | 0.175104 |
| 5 | 1 | cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8 | [42, 24, 1] | [32, 2, 1] | 0.133120 |
| 6 | 1 | cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8 | [43, 25, 1] | [32, 2, 1] | 0.136192 |
| 7 | 2 | cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8 | [21, 12, 1] | [32, 4, 1] | 0.125440 |
| 8 | 2 | cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8 | [22, 13, 1] | [32, 4, 1] | 0.106496 |
| 9 | 3 | cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8 | [11, 6, 1] | [32, 8, 1] | 0.139264 |
| 10 | 3 | cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8 | [11, 7, 1] | [32, 8, 1] | 0.111616 |
| 11 | 4 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | [6, 3, 2] | [32, 4, 1] | 0.039936 |
| 12 | 4 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.034816 |
| 13 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 3, 4] | [32, 4, 1] | 0.043008 |
| 14 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [12, 3, 1] | [32, 8, 1] | 0.019456 |
| 15 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.035840 |
| 16 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.037888 |
| 17 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 4, 4] | [32, 4, 1] | 0.044544 |
| 18 | 4 | cc_split_swin_16h_proj_pool_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.048128 |
| 19 | 4 | cc_split_swin_16h_final_head_512_wait_fp8 | [12, 2, 1] | [32, 8, 1] | 0.023552 |
| 20 | 5 | cc_vit_1d_repack_2d_to_1d_fp8 | [288, 1, 1] | [256, 1, 1] | 0.005120 |
| 21 | 5 | cc_vit_1d_ffn_expand_publish_fp8 | [96, 1, 1] | [32, 4, 1] | 0.070656 |
| 22 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.067584 |
| 23 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.052224 |
| 24 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.026624 |
| 25 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.044544 |
| 26 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055808 |
| 27 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.070656 |
| 28 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.052224 |
| 29 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.026624 |
| 30 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.044544 |
| 31 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055808 |
| 32 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.070656 |
| 33 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.052224 |
| 34 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.026624 |
| 35 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.043008 |
| 36 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.054272 |
| 37 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068608 |
| 38 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.052224 |
| 39 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.026624 |
| 40 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.045056 |
| 41 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.064512 |
| 42 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.067072 |
| 43 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.046592 |
| 44 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.022528 |
| 45 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.042496 |
| 46 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.066560 |
| 47 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068608 |
| 48 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.044544 |
| 49 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.024064 |
| 50 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.041984 |
| 51 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.073216 |
| 52 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068608 |
| 53 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.038400 |
| 54 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.020992 |
| 55 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.043008 |
| 56 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.075776 |
| 57 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068096 |
| 58 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.037376 |
| 59 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.019968 |
| 60 | 5 | cc_vit_1d_projection_wait_fp8 | [24, 1, 4] | [32, 4, 1] | 0.040960 |
| 61 | 5 | cc_vit_1d_repack_1d_to_2d_fp8 | [288, 1, 1] | [256, 1, 1] | 0.004096 |
| 62 | 6 | cc_dec_input_upsample_1024_512_tilesync_fp8 | [12, 3, 4] | [32, 2, 1] | 0.031744 |
| 63 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.037888 |
| 64 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.031232 |
| 65 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 3, 4] | [32, 4, 1] | 0.067584 |
| 66 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [12, 3, 1] | [32, 8, 1] | 0.009728 |
| 67 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.031232 |
| 68 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.037376 |
| 69 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 4, 4] | [32, 4, 1] | 0.068096 |
| 70 | 4 | cc_split_swin_16h_proj_512_outview_wait_fp8 | [12, 3, 1] | [32, 4, 1] | 0.023552 |
| 71 | 3 | cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8 | [11, 6, 1] | [32, 8, 1] | 0.168960 |
| 72 | 3 | cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8 | [11, 7, 1] | [32, 8, 1] | 0.080896 |
| 73 | 2 | cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8 | [22, 12, 1] | [32, 4, 1] | 0.138752 |
| 74 | 2 | cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8 | [21, 13, 1] | [32, 4, 1] | 0.097280 |
| 75 | 1 | cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8 | [43, 24, 1] | [32, 2, 1] | 0.150528 |
| 76 | 1 | cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8 | [42, 25, 1] | [32, 2, 1] | 0.117760 |
| 77 | 0 | cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8 | [85, 48, 1] | [32, 1, 1] | 0.158208 |
| 78 | 0 | cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8 | [84, 49, 1] | [32, 1, 1] | 0.155648 |
| 79 | 0 | cc_tinlayout_fused_post_block_swin_1h_32_fp8 | [169, 97, 1] | [32, 1, 1] | 0.591872 |
| 80 | 14 | cg2r_copy_kernel | [80, 45, 1] | [16, 16, 1] | 0.015360 |
| 81 | 13 | cg2r_post_process_kernel | [80, 45, 1] | [16, 16, 1] | 0.056320 |

## 1920: all actual launches

| Order | FB | Kernel | Grid | Block | Median ms |
|---:|---:|---|---|---|---:|
| 0 | 14 | cg2r_copy_kernel | [120, 68, 1] | [16, 16, 1] | 0.044032 |
| 1 | 6 | cc_cb_clear | [143, 1, 1] | [256, 1, 1] | 0.002048 |
| 2 | 0 | cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8 | [240, 144, 1] | [32, 1, 1] | 1.367040 |
| 3 | 0 | cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8 | [120, 72, 1] | [32, 1, 1] | 0.317952 |
| 4 | 0 | cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8 | [121, 73, 1] | [32, 1, 1] | 0.366080 |
| 5 | 1 | cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8 | [60, 36, 1] | [32, 2, 1] | 0.272896 |
| 6 | 1 | cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8 | [61, 37, 1] | [32, 2, 1] | 0.288768 |
| 7 | 2 | cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8 | [30, 18, 1] | [32, 4, 1] | 0.243712 |
| 8 | 2 | cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8 | [31, 19, 1] | [32, 4, 1] | 0.238592 |
| 9 | 3 | cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8 | [15, 9, 1] | [32, 8, 1] | 0.231936 |
| 10 | 3 | cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8 | [16, 10, 1] | [32, 8, 1] | 0.294912 |
| 11 | 4 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | [8, 5, 2] | [32, 4, 1] | 0.059392 |
| 12 | 4 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.033792 |
| 13 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.087040 |
| 14 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [16, 5, 1] | [32, 8, 1] | 0.030720 |
| 15 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.063488 |
| 16 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.031744 |
| 17 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.088064 |
| 18 | 4 | cc_split_swin_16h_proj_pool_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.020480 |
| 19 | 4 | cc_split_swin_16h_final_head_512_wait_fp8 | [16, 3, 1] | [32, 8, 1] | 0.018432 |
| 20 | 5 | cc_vit_1d_repack_2d_to_1d_fp8 | [640, 1, 1] | [256, 1, 1] | 0.008192 |
| 21 | 5 | cc_vit_1d_ffn_expand_publish_fp8 | [160, 1, 1] | [32, 4, 1] | 0.136704 |
| 22 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.091136 |
| 23 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.070656 |
| 24 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.047104 |
| 25 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.040448 |
| 26 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.118784 |
| 27 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.098304 |
| 28 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.064512 |
| 29 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 30 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.044544 |
| 31 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.119808 |
| 32 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.096768 |
| 33 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 34 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 35 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.043520 |
| 36 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.118784 |
| 37 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097280 |
| 38 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 39 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 40 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.044032 |
| 41 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.118784 |
| 42 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097280 |
| 43 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 44 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 45 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.041984 |
| 46 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.119808 |
| 47 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.096768 |
| 48 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 49 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 50 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.044032 |
| 51 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.118784 |
| 52 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.096256 |
| 53 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.066560 |
| 54 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 55 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.043008 |
| 56 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.118784 |
| 57 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097280 |
| 58 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 59 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 60 | 5 | cc_vit_1d_projection_wait_fp8 | [40, 1, 4] | [32, 4, 1] | 0.045056 |
| 61 | 5 | cc_vit_1d_repack_1d_to_2d_fp8 | [640, 1, 1] | [256, 1, 1] | 0.006656 |
| 62 | 6 | cc_dec_input_upsample_1024_512_tilesync_fp8 | [16, 5, 4] | [32, 2, 1] | 0.041472 |
| 63 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.072192 |
| 64 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.044032 |
| 65 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.094720 |
| 66 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [16, 5, 1] | [32, 8, 1] | 0.027648 |
| 67 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.063488 |
| 68 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.038912 |
| 69 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.097280 |
| 70 | 4 | cc_split_swin_16h_proj_512_outview_wait_fp8 | [16, 5, 1] | [32, 4, 1] | 0.032768 |
| 71 | 3 | cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8 | [16, 9, 1] | [32, 8, 1] | 0.270336 |
| 72 | 3 | cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8 | [15, 10, 1] | [32, 8, 1] | 0.314880 |
| 73 | 2 | cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8 | [31, 18, 1] | [32, 4, 1] | 0.267776 |
| 74 | 2 | cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8 | [30, 19, 1] | [32, 4, 1] | 0.215040 |
| 75 | 1 | cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8 | [61, 36, 1] | [32, 2, 1] | 0.311808 |
| 76 | 1 | cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8 | [60, 37, 1] | [32, 2, 1] | 0.269312 |
| 77 | 0 | cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8 | [121, 72, 1] | [32, 1, 1] | 0.338944 |
| 78 | 0 | cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8 | [120, 73, 1] | [32, 1, 1] | 0.328704 |
| 79 | 0 | cc_tinlayout_fused_post_block_swin_1h_32_fp8 | [241, 145, 1] | [32, 1, 1] | 1.321984 |
| 80 | 14 | cg2r_copy_kernel | [120, 68, 1] | [16, 16, 1] | 0.044032 |
| 81 | 13 | cg2r_post_process_kernel | [120, 68, 1] | [16, 16, 1] | 0.125952 |

# V2.2 actual NVAPI D3D12 launch ledger

50 warmup / 20 measured frames; D3D12 timestamps bracket each unmodified single-kernel LaunchCuKernelChain call. Native CUDA export hooks observed no launches; NVAPI CreateCuModule/CreateCuFunction resolves names. GPU timestamp intervals include dispatch-local overhead; they are not instruction stall counters.

| Width | FB | Calls/frame | Median aggregate ms |
|---:|---:|---:|---:|
| 1280 | 5 | 42 | 1.972224 |
| 1280 | 0 | 6 | 1.819136 |
| 1280 | 4 | 17 | 0.620544 |
| 1280 | 1 | 4 | 0.527360 |
| 1280 | 3 | 4 | 0.484352 |
| 1280 | 2 | 4 | 0.455168 |
| 1280 | 13 | 1 | 0.056320 |
| 1280 | 14 | 2 | 0.033792 |
| 1280 | 6 | 2 | 0.032768 |
| 1920 | 0 | 6 | 4.037632 |
| 1920 | 5 | 42 | 3.012608 |
| 1920 | 1 | 4 | 1.132032 |
| 1920 | 3 | 4 | 1.079296 |
| 1920 | 2 | 4 | 0.948736 |
| 1920 | 4 | 17 | 0.893952 |
| 1920 | 13 | 1 | 0.128000 |
| 1920 | 14 | 2 | 0.088064 |
| 1920 | 6 | 2 | 0.045056 |

## 1280: all actual launches

| Order | FB | Kernel | Grid | Block | Median ms |
|---:|---:|---|---|---|---:|
| 0 | 14 | cg2r_copy_kernel | [80, 45, 1] | [16, 16, 1] | 0.018432 |
| 1 | 6 | cc_cb_clear | [84, 1, 1] | [256, 1, 1] | 0.002048 |
| 2 | 0 | cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8 | [168, 96, 1] | [32, 1, 1] | 0.605184 |
| 3 | 0 | cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8 | [84, 48, 1] | [32, 1, 1] | 0.142336 |
| 4 | 0 | cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8 | [85, 49, 1] | [32, 1, 1] | 0.172032 |
| 5 | 1 | cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8 | [42, 24, 1] | [32, 2, 1] | 0.130048 |
| 6 | 1 | cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8 | [43, 25, 1] | [32, 2, 1] | 0.133120 |
| 7 | 2 | cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8 | [21, 12, 1] | [32, 4, 1] | 0.122880 |
| 8 | 2 | cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8 | [22, 13, 1] | [32, 4, 1] | 0.101376 |
| 9 | 3 | cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8 | [11, 6, 1] | [32, 8, 1] | 0.135168 |
| 10 | 3 | cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8 | [11, 7, 1] | [32, 8, 1] | 0.107520 |
| 11 | 4 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | [6, 3, 2] | [32, 4, 1] | 0.038912 |
| 12 | 4 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.034816 |
| 13 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 3, 4] | [32, 4, 1] | 0.041984 |
| 14 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [12, 3, 1] | [32, 8, 1] | 0.019456 |
| 15 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.037888 |
| 16 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.036864 |
| 17 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 4, 4] | [32, 4, 1] | 0.043520 |
| 18 | 4 | cc_split_swin_16h_proj_pool_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.044032 |
| 19 | 4 | cc_split_swin_16h_final_head_512_wait_fp8 | [12, 2, 1] | [32, 8, 1] | 0.022528 |
| 20 | 5 | cc_vit_1d_repack_2d_to_1d_fp8 | [288, 1, 1] | [256, 1, 1] | 0.005120 |
| 21 | 5 | cc_vit_1d_ffn_expand_publish_fp8 | [96, 1, 1] | [32, 4, 1] | 0.069120 |
| 22 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.066560 |
| 23 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.051200 |
| 24 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 25 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.046080 |
| 26 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.054272 |
| 27 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.069632 |
| 28 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.051200 |
| 29 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 30 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.045568 |
| 31 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055296 |
| 32 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068608 |
| 33 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.051200 |
| 34 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 35 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.044032 |
| 36 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.056320 |
| 37 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.067584 |
| 38 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.050176 |
| 39 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 40 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.042496 |
| 41 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055808 |
| 42 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.066048 |
| 43 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.050688 |
| 44 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025088 |
| 45 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.042496 |
| 46 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055808 |
| 47 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.068608 |
| 48 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.049664 |
| 49 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.024576 |
| 50 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.039936 |
| 51 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055296 |
| 52 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.067584 |
| 53 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.051200 |
| 54 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 55 | 5 | cc_vit_1d_projection_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.042496 |
| 56 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [96, 1, 1] | [32, 4, 1] | 0.055296 |
| 57 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [24, 1, 4] | [32, 4, 1] | 0.067584 |
| 58 | 5 | cc_vit_1d_qkv_chained_fp8 | [48, 1, 2] | [32, 4, 1] | 0.051200 |
| 59 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 2, 1] | [32, 4, 1] | 0.025600 |
| 60 | 5 | cc_vit_1d_projection_wait_fp8 | [24, 1, 4] | [32, 4, 1] | 0.043008 |
| 61 | 5 | cc_vit_1d_repack_1d_to_2d_fp8 | [288, 1, 1] | [256, 1, 1] | 0.005120 |
| 62 | 6 | cc_dec_input_upsample_1024_512_tilesync_fp8 | [12, 3, 4] | [32, 2, 1] | 0.030720 |
| 63 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.036864 |
| 64 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.033792 |
| 65 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 3, 4] | [32, 4, 1] | 0.064512 |
| 66 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [12, 3, 1] | [32, 8, 1] | 0.018432 |
| 67 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [6, 3, 2] | [32, 8, 1] | 0.029696 |
| 68 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [12, 3, 1] | [32, 4, 1] | 0.036864 |
| 69 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [6, 4, 4] | [32, 4, 1] | 0.066560 |
| 70 | 4 | cc_split_swin_16h_proj_512_outview_wait_fp8 | [12, 3, 1] | [32, 4, 1] | 0.022528 |
| 71 | 3 | cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8 | [11, 6, 1] | [32, 8, 1] | 0.161792 |
| 72 | 3 | cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8 | [11, 7, 1] | [32, 8, 1] | 0.079872 |
| 73 | 2 | cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8 | [22, 12, 1] | [32, 4, 1] | 0.136192 |
| 74 | 2 | cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8 | [21, 13, 1] | [32, 4, 1] | 0.093184 |
| 75 | 1 | cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8 | [43, 24, 1] | [32, 2, 1] | 0.146432 |
| 76 | 1 | cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8 | [42, 25, 1] | [32, 2, 1] | 0.114688 |
| 77 | 0 | cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8 | [85, 48, 1] | [32, 1, 1] | 0.154624 |
| 78 | 0 | cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8 | [84, 49, 1] | [32, 1, 1] | 0.153088 |
| 79 | 0 | cc_tinlayout_fused_post_block_swin_1h_32_fp8 | [169, 97, 1] | [32, 1, 1] | 0.590336 |
| 80 | 14 | cg2r_copy_kernel | [80, 45, 1] | [16, 16, 1] | 0.015360 |
| 81 | 13 | cg2r_post_process_kernel | [80, 45, 1] | [16, 16, 1] | 0.056320 |

## 1920: all actual launches

| Order | FB | Kernel | Grid | Block | Median ms |
|---:|---:|---|---|---|---:|
| 0 | 14 | cg2r_copy_kernel | [120, 68, 1] | [16, 16, 1] | 0.044032 |
| 1 | 6 | cc_cb_clear | [143, 1, 1] | [256, 1, 1] | 0.002048 |
| 2 | 0 | cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8 | [240, 144, 1] | [32, 1, 1] | 1.370624 |
| 3 | 0 | cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8 | [120, 72, 1] | [32, 1, 1] | 0.317440 |
| 4 | 0 | cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8 | [121, 73, 1] | [32, 1, 1] | 0.359936 |
| 5 | 1 | cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8 | [60, 36, 1] | [32, 2, 1] | 0.272384 |
| 6 | 1 | cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8 | [61, 37, 1] | [32, 2, 1] | 0.285696 |
| 7 | 2 | cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8 | [30, 18, 1] | [32, 4, 1] | 0.240640 |
| 8 | 2 | cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8 | [31, 19, 1] | [32, 4, 1] | 0.232448 |
| 9 | 3 | cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8 | [15, 9, 1] | [32, 8, 1] | 0.229376 |
| 10 | 3 | cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8 | [16, 10, 1] | [32, 8, 1] | 0.286208 |
| 11 | 4 | cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8 | [8, 5, 2] | [32, 4, 1] | 0.059392 |
| 12 | 4 | cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.029696 |
| 13 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.089088 |
| 14 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [16, 5, 1] | [32, 8, 1] | 0.037888 |
| 15 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.055296 |
| 16 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.033792 |
| 17 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.090624 |
| 18 | 4 | cc_split_swin_16h_proj_pool_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.019456 |
| 19 | 4 | cc_split_swin_16h_final_head_512_wait_fp8 | [16, 3, 1] | [32, 8, 1] | 0.018432 |
| 20 | 5 | cc_vit_1d_repack_2d_to_1d_fp8 | [640, 1, 1] | [256, 1, 1] | 0.008192 |
| 21 | 5 | cc_vit_1d_ffn_expand_publish_fp8 | [160, 1, 1] | [32, 4, 1] | 0.133120 |
| 22 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.101376 |
| 23 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065024 |
| 24 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.045056 |
| 25 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.046080 |
| 26 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.121344 |
| 27 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.098304 |
| 28 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.064512 |
| 29 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044032 |
| 30 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.045056 |
| 31 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.122880 |
| 32 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097792 |
| 33 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.063488 |
| 34 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044032 |
| 35 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.045568 |
| 36 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.121344 |
| 37 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097280 |
| 38 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.066048 |
| 39 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044032 |
| 40 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.047104 |
| 41 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.119808 |
| 42 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.098304 |
| 43 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.064512 |
| 44 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044032 |
| 45 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.044544 |
| 46 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.120832 |
| 47 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.097792 |
| 48 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065024 |
| 49 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044544 |
| 50 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.046592 |
| 51 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.120832 |
| 52 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.098304 |
| 53 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.065536 |
| 54 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.043008 |
| 55 | 5 | cc_vit_1d_projection_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.046592 |
| 56 | 5 | cc_vit_1d_ffn_expand_chained_fp8 | [160, 1, 1] | [32, 4, 1] | 0.119808 |
| 57 | 5 | cc_vit_1d_ffn_contract_chained_fp8 | [40, 1, 4] | [32, 4, 1] | 0.098304 |
| 58 | 5 | cc_vit_1d_qkv_chained_fp8 | [80, 1, 2] | [32, 4, 1] | 0.064512 |
| 59 | 5 | cc_vit_1d_attention_chained_fp8 | [32, 3, 1] | [32, 4, 1] | 0.044032 |
| 60 | 5 | cc_vit_1d_projection_wait_fp8 | [40, 1, 4] | [32, 4, 1] | 0.043008 |
| 61 | 5 | cc_vit_1d_repack_1d_to_2d_fp8 | [640, 1, 1] | [256, 1, 1] | 0.007168 |
| 62 | 6 | cc_dec_input_upsample_1024_512_tilesync_fp8 | [16, 5, 4] | [32, 2, 1] | 0.043008 |
| 63 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.068608 |
| 64 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.046080 |
| 65 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.096768 |
| 66 | 4 | cc_split_swin_16h_proj_512_chained_fp8 | [16, 5, 1] | [32, 8, 1] | 0.027648 |
| 67 | 4 | cc_split_swin_16h_ffwd_512_chained_fp8 | [8, 5, 2] | [32, 8, 1] | 0.061440 |
| 68 | 4 | cc_split_swin_16h_ffwd_proj_512_chained_fp8 | [16, 5, 1] | [32, 4, 1] | 0.041984 |
| 69 | 4 | cc_split_swin_16h_qkv_512_chained_fp8 | [8, 5, 4] | [32, 4, 1] | 0.094208 |
| 70 | 4 | cc_split_swin_16h_proj_512_outview_wait_fp8 | [16, 5, 1] | [32, 4, 1] | 0.030208 |
| 71 | 3 | cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8 | [16, 9, 1] | [32, 8, 1] | 0.254976 |
| 72 | 3 | cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8 | [15, 10, 1] | [32, 8, 1] | 0.308224 |
| 73 | 2 | cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8 | [31, 18, 1] | [32, 4, 1] | 0.265216 |
| 74 | 2 | cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8 | [30, 19, 1] | [32, 4, 1] | 0.210944 |
| 75 | 1 | cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8 | [61, 36, 1] | [32, 2, 1] | 0.308736 |
| 76 | 1 | cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8 | [60, 37, 1] | [32, 2, 1] | 0.265216 |
| 77 | 0 | cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8 | [121, 72, 1] | [32, 1, 1] | 0.335872 |
| 78 | 0 | cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8 | [120, 73, 1] | [32, 1, 1] | 0.329728 |
| 79 | 0 | cc_tinlayout_fused_post_block_swin_1h_32_fp8 | [241, 145, 1] | [32, 1, 1] | 1.329664 |
| 80 | 14 | cg2r_copy_kernel | [120, 68, 1] | [16, 16, 1] | 0.043520 |
| 81 | 13 | cg2r_post_process_kernel | [120, 68, 1] | [16, 16, 1] | 0.128000 |

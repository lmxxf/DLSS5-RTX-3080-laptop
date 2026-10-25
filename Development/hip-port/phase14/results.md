# Phase14 formal controls

Small31/Style1, Graph off, defaultDVFS140W cap,50warmup/80iter. PROFILE_TOTAL is a separate instrumented frame. Both720 paths are corrected; wrong Phase12720 output is not used for quality.

| Variant | Width | GPU min / median | Wall med | PROFILE_TOTAL | Attention entry | SM MHz med | Power W med | Temp C med |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| baseline-confirm | 1600 | 23.239 / 23.640 | 23.722 | 21.630976 | vit_attention_fused_640_bytein_bout | 1590.0 | 139.53 | 69.0 |
| baseline-confirm | 1920 | 31.287 / 31.681 | 31.836 | 28.406816 | vit_attention_fused_640_bytein_bout | 1537.5 | 139.82 | 73.0 |
| baseline-confirm-reverse | 1600 | 23.799 / 23.998 | 24.072 | 21.764096 | vit_attention_fused_640_bytein_bout | 1552.5 | 139.86 | 76.5 |
| baseline-confirm-reverse | 1920 | 31.524 / 32.100 | 32.225 | 28.738560 | vit_attention_fused_640_bytein_bout | 1530.0 | 139.69 | 79.0 |
| baseline-final | 1280 | 13.957 / 14.105 | 14.205 | 13.448192 | vit_attention_fused_400_bytein_bout | 1605.0 | 131.65 | 64.0 |
| baseline-final | 1600 | 23.183 / 23.588 | 23.696 | 21.629952 | vit_attention_fused_640_bytein_bout | 1575.0 | 139.22 | 68.0 |
| baseline-final | 1920 | 31.222 / 31.801 | 31.899 | 29.022208 | vit_attention_fused_640_bytein_bout | 1537.5 | 139.60500000000002 | 72.5 |
| baseline-final-reverse | 1280 | 14.214 / 14.390 | 14.476 | 13.420544 | vit_attention_fused_400_bytein_bout | 1590.0 | 139.62 | 75.0 |
| baseline-final-reverse | 1600 | 23.622 / 24.054 | 24.136 | 21.767168 | vit_attention_fused_640_bytein_bout | 1560.0 | 139.14499999999998 | 76.5 |
| baseline-final-reverse | 1920 | 31.557 / 32.083 | 32.190 | 28.516384 | vit_attention_fused_640_bytein_bout | 1530.0 | 139.695 | 78.5 |
| cap256-abba-a | 1280 | 13.987 / 14.142 | 14.220 | 13.411360 | vit_attention_fused_256_bytein_bout | 1605.0 | 132.43 | 64.0 |
| cap256-abba-a2 | 1280 | 14.012 / 14.261 | 14.359 | 13.777920 | vit_attention_fused_256_bytein_bout | 1605.0 | 126.58 | 69.0 |
| cap256-forward | 1280 | 13.886 / 14.114 | 14.196 | 13.593600 | vit_attention_fused_256_bytein_bout | 1635.0 | 133.15 | 64.0 |
| cap256-reverse | 1280 | 13.989 / 14.222 | 14.311 | 14.389248 | vit_attention_fused_256_bytein_bout | 1605.0 | 139.79 | 69.0 |
| cap400-abba-b1 | 1280 | 13.974 / 14.141 | 14.220 | 13.659136 | vit_attention_fused_400_bytein_bout | 1620.0 | 139.86 | 66.0 |
| cap400-abba-b2 | 1280 | 13.981 / 14.178 | 14.274 | 13.452288 | vit_attention_fused_400_bytein_bout | 1612.5 | 130.04 | 67.5 |
| cap400-forward | 1280 | 13.924 / 14.115 | 14.208 | 13.300736 | vit_attention_fused_400_bytein_bout | 1620.0 | 139.37 | 66.0 |
| cap400-reverse | 1280 | 13.970 / 14.121 | 14.220 | 13.686784 | vit_attention_fused_400_bytein_bout | 1620.0 | 131.92 | 67.0 |
| control256-final | 1280 | 14.006 / 14.182 | 14.264 | 13.627392 | vit_attention_fused_256_bytein_bout | 1605.0 | 134.2 | 65.0 |
| control256-final-reverse | 1280 | 14.368 / 14.424 | 14.517 | 13.995008 | vit_attention_fused_256_bytein_bout | 1590.0 | 139.63 | 75.0 |
| default400 | 1280 | 14.076 / 14.147 | 14.245 | 13.498368 | vit_attention_fused_400_bytein_bout | 1620.0 | 139.66 | 67.0 |
| default400 | 1600 | 23.375 / 23.722 | 23.882 | 22.387712 | vit_attention_fused_640_bytein_bout | 1575.0 | 139.79 | 71.0 |
| default400 | 1920 | 31.347 / 31.826 | 31.926 | 28.646400 | vit_attention_fused_640_bytein_bout | 1545.0 | 139.69 | 75.0 |
| default400-reverse | 1280 | 14.204 / 14.381 | 14.468 | 13.714240 | vit_attention_fused_400_bytein_bout | 1590.0 | 139.69 | 75.0 |
| default400-reverse | 1600 | 23.586 / 23.885 | 23.996 | 21.772288 | vit_attention_fused_640_bytein_bout | 1560.0 | 139.28 | 76.0 |
| default400-reverse | 1920 | 31.250 / 32.111 | 32.206 | 28.637216 | vit_attention_fused_640_bytein_bout | 1530.0 | 139.685 | 78.0 |
| selected | 1280 | 14.021 / 14.166 | 14.247 | 13.408288 | vit_attention_fused_256_bytein_bout | 1620.0 | 139.53 | 66.0 |
| selected | 1600 | 23.361 / 23.642 | 23.758 | 21.702656 | vit_attention_fused_640_bytein_bout | 1582.5 | 139.54 | 70.0 |
| selected | 1920 | 31.350 / 31.824 | 31.955 | 28.379137 | vit_attention_fused_640_bytein_bout | 1537.5 | 139.185 | 74.0 |
| selected-reverse | 1280 | 14.249 / 14.426 | 14.519 | 14.326784 | vit_attention_fused_256_bytein_bout | 1590.0 | 139.44 | 75.0 |
| selected-reverse | 1600 | 23.597 / 24.016 | 24.147 | 21.770272 | vit_attention_fused_640_bytein_bout | 1545.0 | 139.14 | 76.0 |
| selected-reverse | 1920 | 31.571 / 31.977 | 32.077 | 28.696576 | vit_attention_fused_640_bytein_bout | 1530.0 | 139.73000000000002 | 77.5 |

## Final default400 1280 kernel profile

| Kernel | Calls | Total ms | Regs | LOCAL B | Shared B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2 | 0.506880 | 168 | 0 | 24576 | 12 |
| c128_wave2_bi_ho | 1 | 0.317440 | 168 | 0 | 24576 | 12 |
| c128_wave2_up_lb_sh | 1 | 0.355328 | 168 | 0 | 24576 | 12 |
| c256_wave2_bi_bo_w16 | 3 | 1.054720 | 226 | 0 | 49152 | 8 |
| c256_wave2_bi_w16 | 1 | 0.371712 | 226 | 0 | 49152 | 8 |
| c32_wave1_finish_b8 | 1 | 0.484352 | 162 | 0 | 8192 | 11 |
| c32_wave1_finish_dcrop_b8d | 1 | 0.501760 | 162 | 0 | 8192 | 11 |
| c32_wave1_mapped_b8 | 1 | 0.491520 | 168 | 0 | 8192 | 11 |
| c32_wave1_post_b8 | 1 | 1.983488 | 168 | 0 | 8192 | 11 |
| c32_wave1_prefix_b8d | 1 | 2.028544 | 168 | 0 | 8192 | 11 |
| c32_wave1_up_b8 | 1 | 0.556032 | 168 | 0 | 10240 | 9 |
| c512_qkv_attention_compact_w16 | 4 | 0.247808 | 128 | 0 | 6144 | 16 |
| c64_wave2_bi_bo_w16 | 1 | 0.329728 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_ho | 1 | 0.418816 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_w16 | 1 | 0.406528 | 168 | 0 | 12288 | 12 |
| c64_wave2_up_lb_sh | 1 | 0.480256 | 168 | 0 | 12288 | 12 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2 | 0.100352 | 48 | 0 | 2176 | 16 |
| mh_attention_project_frag_c512_w16_u4 | 1 | 0.023552 | 120 | 0 | 0 | 16 |
| mh_attention_project_frag_c512_w16_u4_bout | 3 | 0.065536 | 120 | 0 | 0 | 16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.051200 | 33 | 0 | 0 | 16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.023552 | 62 | 0 | 2176 | 32 |
| mh_pool_project_group_c256_out8_f8w16 | 1 | 0.024576 | 62 | 0 | 4224 | 32 |
| mh_pool_project_group_c512_out8_f8w16 | 1 | 0.030720 | 62 | 0 | 8320 | 32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.040960 | 62 | 0 | 1152 | 32 |
| split_ffn_one_w2f8_w16_bin | 4 | 0.219136 | 105 | 0 | 0 | 16 |
| split_projection_frag_w16_bskip | 4 | 0.091136 | 119 | 0 | 1024 | 16 |
| vit_attention_fused_400_bytein_bout | 8 | 0.264192 | 119 | 0 | 0 | 16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 0.518144 | 80 | 0 | 0 | 16 |
| vit_gather_b8 | 2 | 0.013312 | 16 | 0 | 0 | 48 |
| vit_stream_contract_frag_bstream_bout | 8 | 0.731136 | 106 | 0 | 4096 | 16 |
| vit_stream_project_n64_bb_bout | 8 | 0.209920 | 101 | 0 | 0 | 16 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 0.556032 | 119 | 0 | 16384 | 15 |

## Final default400 1600 kernel profile

| Kernel | Calls | Total ms | Regs | LOCAL B | Shared B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2 | 0.806912 | 168 | 0 | 24576 | 12 |
| c128_wave2_bi_ho | 1 | 0.514048 | 168 | 0 | 24576 | 12 |
| c128_wave2_up_lb_sh | 1 | 0.524288 | 168 | 0 | 24576 | 12 |
| c256_wave2_bi_bo_w16 | 3 | 1.837056 | 226 | 0 | 49152 | 8 |
| c256_wave2_bi_w16 | 1 | 0.549888 | 226 | 0 | 49152 | 8 |
| c32_wave1_finish_b8 | 1 | 0.794624 | 162 | 0 | 8192 | 11 |
| c32_wave1_finish_dcrop_b8d | 1 | 0.812032 | 162 | 0 | 8192 | 11 |
| c32_wave1_mapped_b8 | 1 | 0.797696 | 168 | 0 | 8192 | 11 |
| c32_wave1_post_b8 | 1 | 3.274752 | 168 | 0 | 8192 | 11 |
| c32_wave1_prefix_b8d | 1 | 3.371008 | 168 | 0 | 8192 | 11 |
| c32_wave1_up_b8 | 1 | 1.308672 | 168 | 0 | 10240 | 9 |
| c512_qkv_attention_compact_w16 | 4 | 0.368640 | 128 | 0 | 6144 | 16 |
| c64_wave2_bi_bo_w16 | 1 | 0.542720 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_ho | 1 | 0.656384 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_w16 | 1 | 0.640000 | 168 | 0 | 12288 | 12 |
| c64_wave2_up_lb_sh | 1 | 0.692224 | 168 | 0 | 12288 | 12 |
| decoder_project2x_h16w_byteout_w | 1 | 0.142336 | 55 | 0 | 2176 | 16 |
| decoder_project2x_h16w_w_bin_f8w16 | 1 | 0.068608 | 48 | 0 | 2176 | 16 |
| mh_attention_project_frag_c512_w16_u4 | 4 | 0.165888 | 120 | 0 | 0 | 16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.079872 | 33 | 0 | 0 | 16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.044032 | 62 | 0 | 2176 | 32 |
| mh_pool_project_group_c256_f8w16 | 1 | 0.034816 | 62 | 0 | 4224 | 32 |
| mh_pool_project_group_c512_out8_f8w16 | 1 | 0.034816 | 62 | 0 | 8320 | 32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.065536 | 62 | 0 | 1152 | 32 |
| split_ffn_one_w2f8_w16 | 4 | 0.386048 | 105 | 0 | 0 | 16 |
| split_projection_frag_w16 | 4 | 0.155648 | 119 | 0 | 1024 | 16 |
| vit_attention_fused_640_bytein_bout | 8 | 0.658432 | 119 | 0 | 0 | 16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 0.798720 | 80 | 0 | 0 | 16 |
| vit_gather_b8 | 2 | 0.019456 | 16 | 0 | 0 | 48 |
| vit_stream_contract_frag_bstream_bout | 8 | 0.946176 | 106 | 0 | 4096 | 16 |
| vit_stream_project_n64_bb_bout | 8 | 0.280576 | 101 | 0 | 0 | 16 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 1.015808 | 119 | 0 | 16384 | 15 |

## Final default400 1920 kernel profile

| Kernel | Calls | Total ms | Regs | LOCAL B | Shared B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2 | 1.052672 | 168 | 0 | 24576 | 12 |
| c128_wave2_bi_ho | 1 | 0.658432 | 168 | 0 | 24576 | 12 |
| c128_wave2_up_lb_sh | 1 | 0.687104 | 168 | 0 | 24576 | 12 |
| c256_wave2_bi_bo_w16 | 3 | 1.723392 | 226 | 0 | 49152 | 8 |
| c256_wave2_bi_w16 | 1 | 0.713728 | 226 | 0 | 49152 | 8 |
| c32_wave1_finish_b8 | 1 | 1.059840 | 162 | 0 | 8192 | 11 |
| c32_wave1_finish_dcrop_b8d | 1 | 1.087488 | 162 | 0 | 8192 | 11 |
| c32_wave1_mapped_b8 | 1 | 1.071104 | 168 | 0 | 8192 | 11 |
| c32_wave1_post_b8 | 1 | 4.646912 | 168 | 0 | 8192 | 11 |
| c32_wave1_prefix_b8d | 1 | 4.538368 | 168 | 0 | 8192 | 11 |
| c32_wave1_up_b8 | 1 | 1.208320 | 168 | 0 | 10240 | 9 |
| c512_qkv_attention_compact_w16 | 4 | 0.453632 | 128 | 0 | 6144 | 16 |
| c64_wave2_bi_bo_w16 | 1 | 0.724992 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_ho | 1 | 0.869376 | 168 | 0 | 12288 | 12 |
| c64_wave2_bi_w16 | 1 | 0.845824 | 168 | 0 | 12288 | 12 |
| c64_wave2_up_lb_sh | 1 | 0.916480 | 168 | 0 | 12288 | 12 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2 | 0.129024 | 48 | 0 | 2176 | 16 |
| mh_attention_project_frag_c512_w16_u4 | 1 | 0.048128 | 120 | 0 | 0 | 16 |
| mh_attention_project_frag_c512_w16_u4_bout | 3 | 0.136192 | 120 | 0 | 0 | 16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.105472 | 33 | 0 | 0 | 16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.052224 | 62 | 0 | 2176 | 32 |
| mh_pool_project_group_c256_out8_f8w16 | 1 | 0.041984 | 62 | 0 | 4224 | 32 |
| mh_pool_project_group_c512_out8_f8w16 | 1 | 0.036864 | 62 | 0 | 8320 | 32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.077824 | 62 | 0 | 1152 | 32 |
| split_ffn_one_w2f8_w16_bin | 4 | 0.313344 | 105 | 0 | 0 | 16 |
| split_projection_frag_w16_bskip | 4 | 0.165888 | 119 | 0 | 1024 | 16 |
| vit_attention_fused_640_bytein_bout | 8 | 1.177600 | 119 | 0 | 0 | 16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 1.131520 | 80 | 0 | 0 | 16 |
| vit_gather_b8 | 2 | 0.024576 | 16 | 0 | 0 | 48 |
| vit_stream_contract_frag_bstream_bout | 8 | 1.207296 | 106 | 0 | 4096 | 16 |
| vit_stream_project_n64_bb_bout | 8 | 0.352256 | 101 | 0 | 0 | 16 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 1.388544 | 119 | 0 | 16384 | 15 |

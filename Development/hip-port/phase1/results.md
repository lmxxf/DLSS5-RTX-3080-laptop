# Phase 1: packed FP16 accumulators

GPU timings exclude initialization/readback; kernel census is a separate instrumented frame.

## 1920x1080 (processing 1920x1152)

F32 median/min 63.342/60.548 ms; F16 63.264/60.024 ms; speedup 1.001x.

Accuracy: `{"padded": {"invalid": 0, "psnr_peak1_db": 46.15421124497031, "maxabs": 0.047580182552337646, "rmse": 0.004923675672127433}, "visible": {"invalid": 0, "psnr_peak1_db": 46.18517383191663, "maxabs": 0.047580182552337646, "rmse": 0.004906155493278832}}`

| Kernel | Calls | F32 ms | F16 ms | Regs F32→F16 | LMem F32→F16 | OccW F32→F16 |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo | 2 | 2.7003 | 2.5928 | 248→239 | 0→0 | 8→8 |
| c128_wave2_bi_ho | 1 | 1.4387 | 1.3957 | 247→239 | 0→0 | 8→8 |
| c128_wave2_up_lb_sh | 1 | 1.5708 | 1.5073 | 247→223 | 0→0 | 8→8 |
| c256_wave2_bi_bo_w16 | 3 | 3.4365 | 3.2512 | 240→241 | 0→0 | 8→8 |
| c256_wave2_bi_w16 | 1 | 1.4100 | 1.3691 | 240→241 | 0→0 | 8→8 |
| c32_wave1_finish_b8 | 1 | 1.8350 | 1.7347 | 168→163 | 0→0 | 9→9 |
| c32_wave1_finish_dcrop_b8d | 1 | 1.9517 | 1.8627 | 168→163 | 0→0 | 9→9 |
| c32_wave1_mapped_b8 | 1 | 1.8842 | 1.8125 | 170→161 | 0→0 | 8→9 |
| c32_wave1_post_b8 | 1 | 7.5612 | 8.4685 | 177→163 | 0→0 | 8→9 |
| c32_wave1_prefix_b8d | 1 | 8.3251 | 8.1428 | 178→170 | 0→0 | 8→8 |
| c32_wave1_up_b8 | 1 | 2.0869 | 2.0255 | 234→234 | 0→0 | 8→8 |
| c512_qkv_attention_compact_w16 | 4 | 1.1356 | 1.7213 | 229→232 | 0→0 | 8→8 |
| c64_wave2_bi | 1 | 2.0992 | 2.0654 | 248→239 | 0→0 | 8→8 |
| c64_wave2_bi_bo | 1 | 1.7193 | 1.6794 | 248→239 | 0→0 | 8→8 |
| c64_wave2_bi_ho | 1 | 1.8330 | 1.7951 | 247→239 | 0→0 | 8→8 |
| c64_wave2_up_lb_sh | 1 | 2.0500 | 1.9661 | 247→223 | 0→0 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2 | 0.3748 | 0.3676 | 71→70 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 1 | 0.1413 | 0.1434 | 133→125 | 0→0 | 12→16 |
| mh_attention_project_frag_c512_w16_u4_bout | 3 | 0.4280 | 0.4280 | 133→125 | 0→0 | 12→16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.1311 | 0.1290 | 44→44 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.0850 | 0.1300 | 121→200 | 0→0 | 16→8 |
| mh_pool_project_group_c256_out8_f8w16 | 1 | 0.0850 | 0.1055 | 121→200 | 0→0 | 16→8 |
| mh_pool_project_group_c512_out8_f8w16 | 1 | 0.0768 | 0.1014 | 121→128 | 0→104 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.1126 | 0.1853 | 121→200 | 0→0 | 16→8 |
| split_ffn_one_w2f8_w16_bin | 4 | 0.8950 | 0.8899 | 149→139 | 0→0 | 12→12 |
| split_projection_frag_w16_bskip | 4 | 0.4024 | 0.3932 | 135→127 | 0→0 | 12→16 |
| vit_attention_fused_640_bytein_bout | 8 | 2.0521 | 2.4627 | 122→106 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 3.1898 | 3.1447 | 119→111 | 0→0 | 16→16 |
| vit_gather_b8 | 2 | 0.0246 | 0.0246 | 16→16 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8 | 3.6895 | 3.6536 | 162→154 | 0→0 | 12→12 |
| vit_stream_project_n64_bb_bout | 8 | 1.4950 | 1.5493 | 218→226 | 0→0 | 8→8 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 3.9854 | 3.8574 | 135→122 | 0→0 | 10→15 |

## 1600x900 (processing 1600x1024)

F32 median/min 46.19/45.725 ms; F16 45.444/45.046 ms; speedup 1.016x.

Accuracy: `{"padded": {"invalid": 0, "psnr_peak1_db": 46.59134312406831, "maxabs": 0.038017332553863525, "rmse": 0.004682015464254383}, "visible": {"invalid": 0, "psnr_peak1_db": 46.6216462431764, "maxabs": 0.038017332553863525, "rmse": 0.0046657094239312075}}`

| Kernel | Calls | F32 ms | F16 ms | Regs F32→F16 | LMem F32→F16 | OccW F32→F16 |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo | 2 | 2.0961 | 2.0500 | 248→239 | 0→0 | 8→8 |
| c128_wave2_bi_ho | 1 | 1.0895 | 1.0619 | 247→239 | 0→0 | 8→8 |
| c128_wave2_up_lb_sh | 1 | 1.2052 | 1.1878 | 247→223 | 0→0 | 8→8 |
| c256_attn_wave | 1 | 0.2970 | 0.2888 | 207→201 | 0→0 | 8→8 |
| c256_attn_wave_bo | 3 | 0.8581 | 0.8407 | 207→201 | 0→0 | 8→8 |
| c32_wave1_finish_b8 | 1 | 1.7111 | 1.3138 | 168→163 | 0→0 | 9→9 |
| c32_wave1_finish_dcrop_b8d | 1 | 1.4612 | 1.3967 | 168→163 | 0→0 | 9→9 |
| c32_wave1_mapped_b8 | 1 | 1.4152 | 1.3558 | 170→161 | 0→0 | 8→9 |
| c32_wave1_post_b8 | 1 | 5.6064 | 5.4948 | 177→163 | 0→0 | 8→9 |
| c32_wave1_prefix_b8d | 1 | 6.2003 | 7.2684 | 178→170 | 0→0 | 8→8 |
| c32_wave1_up_b8 | 1 | 1.5493 | 1.5288 | 234→234 | 0→0 | 8→8 |
| c512_qkv_attention_compact_w16 | 4 | 0.9247 | 0.8632 | 229→232 | 0→0 | 8→8 |
| c64_wave2_bi | 1 | 1.5340 | 1.5278 | 248→239 | 0→0 | 8→8 |
| c64_wave2_bi_bo | 1 | 1.2902 | 1.2585 | 248→239 | 0→0 | 8→8 |
| c64_wave2_bi_ho | 1 | 1.3783 | 1.3476 | 247→239 | 0→0 | 8→8 |
| c64_wave2_up_lb_sh | 1 | 1.5053 | 1.4868 | 247→223 | 0→0 | 8→8 |
| decoder_project2x_h16w_byteout_w | 1 | 0.2140 | 0.2120 | 58→55 | 0→0 | 16→16 |
| decoder_project2x_h16w_w | 1 | 0.2519 | 0.2570 | 58→55 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 4 | 0.4813 | 0.4895 | 133→125 | 0→0 | 12→16 |
| mh_ffn_fused_c256_frag_project_mapped_g128_qkv_bytein_fb | 4 | 3.0505 | 3.0874 | 128→128 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.0983 | 0.0983 | 44→44 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.0707 | 0.1024 | 121→200 | 0→0 | 16→8 |
| mh_pool_project_group_c256_f8w16 | 1 | 0.0758 | 0.1065 | 121→200 | 0→0 | 16→8 |
| mh_pool_project_group_c512_f8w16 | 1 | 0.0778 | 0.0993 | 121→128 | 0→104 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.0901 | 0.1403 | 121→200 | 0→0 | 16→8 |
| split_ffn_one_w2f8_w16 | 4 | 0.8059 | 0.7926 | 214→197 | 0→0 | 8→8 |
| split_projection_frag_w16 | 4 | 0.3451 | 0.3564 | 135→127 | 0→0 | 12→16 |
| vit_attention_fused_640_bytein_bout | 8 | 1.1530 | 1.1397 | 122→106 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 2.2774 | 3.3823 | 119→111 | 0→0 | 16→16 |
| vit_gather | 2 | 0.0297 | 0.0266 | 10→10 | 0→0 | 48→48 |
| vit_pack_input | 8 | 0.0563 | 0.0553 | 16→16 | 0→0 | 48→48 |
| vit_stream_contract_frag_bout | 8 | 2.1053 | 1.9651 | 134→117 | 0→0 | 12→16 |
| vit_stream_project_n64_bb | 8 | 1.1663 | 1.1530 | 223→210 | 0→0 | 8→8 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 2.8211 | 2.7628 | 135→122 | 0→0 | 10→15 |


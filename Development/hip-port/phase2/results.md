# Phase 2: static weights / exact ones / packed partition sums

GPU timings exclude initialization/readback; kernel census is a separate instrumented frame.

## 1920x1080 (processing 1920x1152)

Phase 1 median/min 59.806/59.245 ms; Phase 2 54.476/53.921 ms; speedup 1.098x.

Accuracy vs Phase 1: `{"padded": {"invalid": 0, "psnr_peak1_db": 48.4813753087198, "maxabs": 0.046734392642974854, "rmse": 0.0037664415707881773}, "visible": {"invalid": 0, "psnr_peak1_db": 48.489389007040764, "maxabs": 0.046734392642974854, "rmse": 0.0037629682124580574}}`

Accuracy vs F32: `{"padded": {"invalid": 0, "psnr_peak1_db": 46.08164586978773, "maxabs": 0.0416027307510376, "rmse": 0.004964982321974246}, "visible": {"invalid": 0, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376, "rmse": 0.004953961711371818}}`

| Kernel | Calls | Phase 1 ms | Phase 2 ms | Regs P1→P2 | LMem P1→P2 | OccW P1→P2 |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo | 2 | 2.5989 | 2.3859 | 239→250 | 0→0 | 8→8 |
| c128_wave2_bi_ho | 1 | 1.3957 | 1.2728 | 239→250 | 0→0 | 8→8 |
| c128_wave2_up_lb_sh | 1 | 1.5145 | 1.4070 | 223→250 | 0→0 | 8→8 |
| c256_wave2_bi_bo_w16 | 3 | 3.2758 | 2.7525 | 241→250 | 0→0 | 8→8 |
| c256_wave2_bi_w16 | 1 | 1.3640 | 1.2073 | 241→250 | 0→0 | 8→8 |
| c32_wave1_finish_b8 | 1 | 1.7490 | 1.5770 | 163→159 | 0→0 | 9→9 |
| c32_wave1_finish_dcrop_b8d | 1 | 1.8657 | 1.6384 | 163→159 | 0→0 | 9→9 |
| c32_wave1_mapped_b8 | 1 | 1.8196 | 1.6599 | 161→146 | 0→0 | 9→9 |
| c32_wave1_post_b8 | 1 | 7.3226 | 6.6785 | 163→160 | 0→0 | 9→9 |
| c32_wave1_prefix_b8d | 1 | 8.1244 | 7.3697 | 170→169 | 0→0 | 8→8 |
| c32_wave1_up_b8 | 1 | 2.0552 | 1.9282 | 234→234 | 0→0 | 8→8 |
| c512_qkv_attention_compact_w16 | 4 | 1.0701 | 0.9472 | 232→229 | 0→0 | 8→8 |
| c64_wave2_bi | 1 | 2.0828 | 1.9118 | 239→250 | 0→0 | 8→8 |
| c64_wave2_bi_bo | 1 | 1.6671 | 1.5032 | 239→250 | 0→0 | 8→8 |
| c64_wave2_bi_ho | 1 | 1.7940 | 1.6077 | 239→250 | 0→0 | 8→8 |
| c64_wave2_up_lb_sh | 1 | 1.9907 | 1.8176 | 223→250 | 0→0 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2 | 0.3799 | 0.3625 | 70→61 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 1 | 0.1423 | 0.1321 | 125→140 | 0→0 | 16→12 |
| mh_attention_project_frag_c512_w16_u4_bout | 3 | 0.4311 | 0.3994 | 125→140 | 0→0 | 16→12 |
| mh_pool_project_c32_b8_out8 | 1 | 0.1290 | 0.1300 | 44→44 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.1290 | 0.0778 | 200→111 | 0→0 | 8→16 |
| mh_pool_project_group_c256_out8_f8w16 | 1 | 0.1055 | 0.0717 | 200→111 | 0→0 | 8→16 |
| mh_pool_project_group_c512_out8_f8w16 | 1 | 0.1014 | 0.0666 | 128→111 | 104→0 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.1853 | 0.1085 | 200→111 | 0→0 | 8→16 |
| split_ffn_one_w2f8_w16_bin | 4 | 0.8745 | 0.8079 | 139→152 | 0→0 | 12→12 |
| split_projection_frag_w16_bskip | 4 | 0.3932 | 0.3707 | 127→145 | 0→0 | 16→12 |
| vit_attention_fused_640_bytein_bout | 8 | 2.0122 | 1.9620 | 106→93 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 3.1549 | 2.8549 | 111→121 | 0→0 | 16→16 |
| vit_gather_b8 | 2 | 0.0246 | 0.0246 | 16→16 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8 | 3.6557 | 3.3864 | 154→217 | 0→0 | 12→8 |
| vit_stream_project_n64_bb_bout | 8 | 1.5258 | 1.3855 | 226→210 | 0→0 | 8→8 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 3.8820 | 3.8441 | 122→119 | 0→0 | 15→15 |

## 1600x900 (processing 1600x1024)

Phase 1 median/min 44.872/44.461 ms; Phase 2 42.264/41.743 ms; speedup 1.062x.

Accuracy vs Phase 1: `{"padded": {"invalid": 0, "psnr_peak1_db": 48.47030135688005, "maxabs": 0.03457203507423401, "rmse": 0.003771246604469662}, "visible": {"invalid": 0, "psnr_peak1_db": 48.52578172915855, "maxabs": 0.03457203507423401, "rmse": 0.003747234859572002}}`

Accuracy vs F32: `{"padded": {"invalid": 0, "psnr_peak1_db": 46.59192049707339, "maxabs": 0.03999394178390503, "rmse": 0.004681704249214074}, "visible": {"invalid": 0, "psnr_peak1_db": 46.62056975312521, "maxabs": 0.03485873341560364, "rmse": 0.004666287706782746}}`

| Kernel | Calls | Phase 1 ms | Phase 2 ms | Regs P1→P2 | LMem P1→P2 | OccW P1→P2 |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo | 2 | 2.0347 | 1.9108 | 239→250 | 0→0 | 8→8 |
| c128_wave2_bi_ho | 1 | 1.0537 | 0.9544 | 239→250 | 0→0 | 8→8 |
| c128_wave2_up_lb_sh | 1 | 1.1796 | 1.1459 | 223→250 | 0→0 | 8→8 |
| c256_attn_wave | 1 | 0.2908 | 0.2724 | 201→250 | 0→0 | 8→8 |
| c256_attn_wave_bo | 3 | 0.8376 | 0.7803 | 201→250 | 0→0 | 8→8 |
| c32_wave1_finish_b8 | 1 | 1.2984 | 1.1581 | 163→159 | 0→0 | 9→9 |
| c32_wave1_finish_dcrop_b8d | 1 | 1.3978 | 1.2308 | 163→159 | 0→0 | 9→9 |
| c32_wave1_mapped_b8 | 1 | 1.3466 | 1.2452 | 161→146 | 0→0 | 9→9 |
| c32_wave1_post_b8 | 1 | 5.4272 | 4.9408 | 163→160 | 0→0 | 9→9 |
| c32_wave1_prefix_b8d | 1 | 6.0324 | 5.4897 | 170→169 | 0→0 | 8→8 |
| c32_wave1_up_b8 | 1 | 1.5155 | 1.4182 | 234→234 | 0→0 | 8→8 |
| c512_qkv_attention_compact_w16 | 4 | 0.8561 | 0.7619 | 232→229 | 0→0 | 8→8 |
| c64_wave2_bi | 1 | 1.5288 | 1.4490 | 239→250 | 0→0 | 8→8 |
| c64_wave2_bi_bo | 1 | 1.2483 | 1.1305 | 239→250 | 0→0 | 8→8 |
| c64_wave2_bi_ho | 1 | 1.3445 | 1.2073 | 239→250 | 0→0 | 8→8 |
| c64_wave2_up_lb_sh | 1 | 1.4746 | 1.3568 | 223→250 | 0→0 | 8→8 |
| decoder_project2x_h16w_byteout_w | 1 | 0.2171 | 0.2099 | 55→55 | 0→0 | 16→16 |
| decoder_project2x_h16w_w | 1 | 0.2540 | 0.2611 | 55→55 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 4 | 0.4854 | 0.4547 | 125→140 | 0→0 | 16→12 |
| mh_ffn_fused_c256_frag_project_mapped_g128_qkv_bytein_fb | 4 | 3.0689 | 2.7423 | 128→128 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 1 | 0.0973 | 0.0973 | 44→44 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1 | 0.1024 | 0.0655 | 200→111 | 0→0 | 8→16 |
| mh_pool_project_group_c256_f8w16 | 1 | 0.1055 | 0.0696 | 200→111 | 0→0 | 8→16 |
| mh_pool_project_group_c512_f8w16 | 1 | 0.0993 | 0.0655 | 128→111 | 104→0 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1 | 0.1413 | 0.0870 | 200→111 | 0→0 | 8→16 |
| split_ffn_one_w2f8_w16 | 4 | 0.7813 | 0.6769 | 197→152 | 0→0 | 8→12 |
| split_projection_frag_w16 | 4 | 0.3523 | 0.3164 | 127→145 | 0→0 | 16→12 |
| vit_attention_fused_640_bytein_bout | 8 | 1.1325 | 1.0967 | 106→93 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8 | 2.2804 | 2.0541 | 111→121 | 0→0 | 16→16 |
| vit_gather | 2 | 0.0297 | 0.0287 | 10→10 | 0→0 | 48→48 |
| vit_pack_input | 8 | 0.0573 | 0.0625 | 16→16 | 0→0 | 48→48 |
| vit_stream_contract_frag_bout | 8 | 1.9620 | 3.1539 | 117→208 | 0→0 | 16→8 |
| vit_stream_project_n64_bb | 8 | 1.1305 | 1.0506 | 210→210 | 0→0 | 8→8 |
| vit_stream_qkv_frag_bin_w5f8 | 8 | 2.7382 | 2.7105 | 122→119 | 0→0 | 15→15 |


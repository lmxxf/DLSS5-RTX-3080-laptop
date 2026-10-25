# Phase 7: branchless FP8 / constant clamps / invariant input decode

50 warmup / 80 iterations, separate instrumented frame. 900p/1080p process 1600×1024 / 1920×1152. Initialization, weights, uploads/readback excluded. Default DVFS; no clock lock.

| Variant | 900p min / median ms | 1080p min / median ms | Bitdiff 900/1080 | Active local-memory kernels 900/1080 |
|---|---:|---:|---:|---:|
| baseline | 27.421 / 27.908 | 36.467 / 36.946 | 0/0 | 0/0 |
| step12 | 27.344 / 27.636 | 36.371 / 36.722 | 0/0 | 0/0 |
| hoist | 27.499 / 27.788 | 36.390 / 36.904 | 0/0 | 0/0 |
| step12-repeat | 27.113 / 27.564 | 35.816 / 36.599 | 0/0 | 0/0 |
| baseline-repeat | 27.757 / 28.173 | 36.655 / 37.330 | 0/0 | 0/0 |
| selected | 27.344 / 27.636 | 36.371 / 36.722 | 0/0 | 0/0 |

## 1600 kernel breakdown

| Kernel | Baseline ms | 1+2 ms | Hoist ms | Regs baseline→1+2→hoist | LMem B | OccW |
|---|---:|---:|---:|---|---|---|
| c128_wave2_bi_bo_w16 | 1.000448 | 0.958464 | 0.961536 | 242→240→240 | 0→0→0 | 8→8→8 |
| c128_wave2_bi_ho | 0.622592 | 0.609280 | 0.609280 | 248→240→240 | 0→0→0 | 8→8→8 |
| c128_wave2_up_lb_sh | 0.694272 | 0.679936 | 0.673792 | 250→240→240 | 0→0→0 | 8→8→8 |
| c256_wave2_bi_bo_w16 | 1.632256 | 1.614848 | 1.624064 | 248→225→225 | 0→0→0 | 8→8→8 |
| c256_wave2_bi_w16 | 0.581632 | 0.577536 | 0.579584 | 248→225→225 | 0→0→0 | 8→8→8 |
| c32_wave1_finish_b8 | 0.993280 | 0.993280 | 1.002496 | 167→167→167 | 0→0→0 | 11→11→11 |
| c32_wave1_finish_dcrop_b8d | 1.019904 | 1.019904 | 1.017856 | 167→167→167 | 0→0→0 | 11→11→11 |
| c32_wave1_mapped_b8 | 1.054720 | 1.037312 | 1.026048 | 168→168→168 | 0→0→0 | 11→11→11 |
| c32_wave1_post_b8 | 4.139008 | 4.052992 | 4.074496 | 167→168→168 | 0→0→0 | 11→11→11 |
| c32_wave1_prefix_b8d | 4.586496 | 4.390912 | 4.367360 | 152→151→151 | 0→0→0 | 9→9→9 |
| c32_wave1_up_b8 | 1.204224 | 1.143808 | 1.143808 | 234→210→210 | 0→0→0 | 8→8→8 |
| c512_qkv_attention_compact_w16 | 0.460800 | 0.401408 | 0.411648 | 203→151→151 | 0→0→0 | 8→12→12 |
| c64_wave2_bi_bo_w16 | 0.690176 | 0.663552 | 0.666624 | 248→234→234 | 0→0→0 | 8→8→8 |
| c64_wave2_bi_ho | 0.835584 | 0.809984 | 0.812032 | 250→241→241 | 0→0→0 | 8→8→8 |
| c64_wave2_bi_w16 | 0.837632 | 0.811008 | 0.811008 | 248→234→234 | 0→0→0 | 8→8→8 |
| c64_wave2_up_lb_sh | 0.921600 | 0.886784 | 0.890880 | 248→239→239 | 0→0→0 | 8→8→8 |
| decoder_project2x_h16w_byteout_w | 0.141312 | 0.145408 | 0.142336 | 55→55→55 | 0→0→0 | 16→16→16 |
| decoder_project2x_h16w_w_bin_f8w16 | 0.068608 | 0.069632 | 0.068608 | 47→47→47 | 0→0→0 | 16→16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.163840 | 0.165920 | 0.167936 | 89→120→120 | 0→0→0 | 16→16→16 |
| mh_pool_project_c32_b8_out8 | 0.089088 | 0.088064 | 0.087040 | 34→33→33 | 0→0→0 | 16→16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.045056 | 0.046080 | 0.045056 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c256_f8w16 | 0.035840 | 0.034816 | 0.034816 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.036864 | 0.035840 | 0.036864 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.068608 | 0.066560 | 0.067584 | 62→62→62 | 0→0→0 | 32→32→32 |
| split_ffn_one_w2f8_w16 | 0.415744 | 0.444416 | 0.445440 | 106→186→186 | 0→0→0 | 16→8→8 |
| split_projection_frag_w16 | 0.150528 | 0.162816 | 0.164864 | 110→119→119 | 0→0→0 | 16→16→16 |
| vit_attention_fused_640_bytein_bout | 0.671744 | 0.690176 | 0.695296 | 78→119→119 | 0→0→0 | 16→16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 0.818176 | 0.817152 | 0.826368 | 80→80→80 | 0→0→0 | 16→16→16 |
| vit_gather_b8 | 0.020480 | 0.019456 | 0.023552 | 16→16→16 | 0→0→0 | 48→48→48 |
| vit_stream_contract_frag_bstream_bout | 0.948224 | 0.950272 | 0.989184 | 106→106→106 | 0→0→0 | 16→16→16 |
| vit_stream_project_n64_bb_bout | 0.287744 | 0.319488 | 0.332800 | 101→138→138 | 0→0→0 | 16→12→12 |
| vit_stream_qkv_frag_bin_w5f8 | 1.019904 | 1.017856 | 1.027072 | 119→119→119 | 0→0→0 | 15→15→15 |

baseline: kernel total 26.256384 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

step12: kernel total 25.724960 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

hoist: kernel total 25.827328 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

step12-repeat: kernel total 25.718784 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

baseline-repeat: kernel total 27.278336 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

selected: kernel total 25.724960 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

## 1920 kernel breakdown

| Kernel | Baseline ms | 1+2 ms | Hoist ms | Regs baseline→1+2→hoist | LMem B | OccW |
|---|---:|---:|---:|---|---|---|
| c128_wave2_bi_bo_w16 | 1.300480 | 1.259520 | 1.261568 | 242→240→240 | 0→0→0 | 8→8→8 |
| c128_wave2_bi_ho | 0.812032 | 0.787456 | 0.792576 | 248→240→240 | 0→0→0 | 8→8→8 |
| c128_wave2_up_lb_sh | 0.891904 | 0.865280 | 0.870400 | 250→240→240 | 0→0→0 | 8→8→8 |
| c256_wave2_bi_bo_w16 | 1.814528 | 1.814528 | 1.817600 | 248→225→225 | 0→0→0 | 8→8→8 |
| c256_wave2_bi_w16 | 0.754688 | 0.751616 | 0.754688 | 248→225→225 | 0→0→0 | 8→8→8 |
| c32_wave1_finish_b8 | 1.323008 | 1.329152 | 1.418240 | 167→167→167 | 0→0→0 | 11→11→11 |
| c32_wave1_finish_dcrop_b8d | 1.352704 | 1.359872 | 1.361920 | 167→167→167 | 0→0→0 | 11→11→11 |
| c32_wave1_mapped_b8 | 1.409024 | 1.386496 | 2.067456 | 168→168→168 | 0→0→0 | 11→11→11 |
| c32_wave1_post_b8 | 5.564416 | 5.463040 | 5.774336 | 167→168→168 | 0→0→0 | 11→11→11 |
| c32_wave1_prefix_b8d | 6.145024 | 5.898240 | 6.379520 | 152→151→151 | 0→0→0 | 9→9→9 |
| c32_wave1_up_b8 | 1.610752 | 1.540096 | 1.631232 | 234→210→210 | 0→0→0 | 8→8→8 |
| c512_qkv_attention_compact_w16 | 0.574464 | 0.496640 | 0.498688 | 203→151→151 | 0→0→0 | 8→12→12 |
| c64_wave2_bi_bo_w16 | 0.919552 | 0.891904 | 0.892928 | 248→234→234 | 0→0→0 | 8→8→8 |
| c64_wave2_bi_ho | 1.100800 | 1.077248 | 1.076224 | 250→241→241 | 0→0→0 | 8→8→8 |
| c64_wave2_bi_w16 | 1.100800 | 1.074176 | 1.143808 | 248→234→234 | 0→0→0 | 8→8→8 |
| c64_wave2_up_lb_sh | 1.229824 | 1.188864 | 1.190912 | 248→239→239 | 0→0→0 | 8→8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 0.136192 | 0.136192 | 0.136192 | 48→48→48 | 0→0→0 | 16→16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.046080 | 0.049152 | 0.048128 | 89→120→120 | 0→0→0 | 16→16→16 |
| mh_attention_project_frag_c512_w16_u4_bout | 0.136192 | 0.139264 | 0.137216 | 89→120→120 | 0→0→0 | 16→16→16 |
| mh_pool_project_c32_b8_out8 | 0.116736 | 0.116736 | 0.115712 | 34→33→33 | 0→0→0 | 16→16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.054272 | 0.053248 | 0.054272 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c256_out8_f8w16 | 0.043008 | 0.041984 | 0.043008 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.037888 | 0.037888 | 0.037888 | 62→62→62 | 0→0→0 | 32→32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.079872 | 0.081920 | 0.080896 | 62→62→62 | 0→0→0 | 32→32→32 |
| split_ffn_one_w2f8_w16_bin | 0.342016 | 0.369664 | 0.372736 | 106→186→186 | 0→0→0 | 16→8→8 |
| split_projection_frag_w16_bskip | 0.159744 | 0.164864 | 0.163840 | 114→119→119 | 0→0→0 | 16→16→16 |
| vit_attention_fused_640_bytein_bout | 1.204224 | 1.244160 | 1.264640 | 78→119→119 | 0→0→0 | 16→16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 1.157120 | 1.116160 | 1.114112 | 80→80→80 | 0→0→0 | 16→16→16 |
| vit_gather_b8 | 0.024576 | 0.023552 | 0.024576 | 16→16→16 | 0→0→0 | 48→48→48 |
| vit_stream_contract_frag_bstream_bout | 1.205248 | 1.212416 | 1.218560 | 106→106→106 | 0→0→0 | 16→16→16 |
| vit_stream_project_n64_bb_bout | 0.362496 | 0.439296 | 0.439296 | 101→138→138 | 0→0→0 | 16→12→12 |
| vit_stream_qkv_frag_bin_w5f8 | 1.401856 | 1.406976 | 1.410048 | 119→119→119 | 0→0→0 | 15→15→15 |

baseline: kernel total 34.411520 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

step12: kernel total 33.817600 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

hoist: kernel total 35.593216 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

step12-repeat: kernel total 34.890752 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

baseline-repeat: kernel total 34.711584 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

selected: kernel total 33.817600 ms; accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

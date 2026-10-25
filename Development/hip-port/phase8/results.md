# Phase 8: direct Ampere D bytes to AB fragments

50 warmup / 80 iterations; separate instrumented frame. 900p/1080p process 1600×1024 / 1920×1152. GPU excludes initialization, weights, transfers/readback. Default DVFS, not clock-locked.

| Variant | 900p min / median ms | 1080p min / median ms | Bitdiff 900/1080 | Nonzero LMem kernel kinds 900/1080 |
|---|---:|---:|---:|---:|
| baseline | 26.962 / 27.390 | 35.645 / 36.467 | 0/0 | 0/0 |
| c32-only | 26.351 / 27.170 | 35.551 / 36.094 | 0/0 | 1/1 |
| layout-only | 26.760 / 26.998 | 35.421 / 35.995 | 0/0 | 1/1 |
| full | 26.901 / 27.170 | 35.658 / 36.045 | 0/0 | 3/3 |
| lowreg | 26.405 / 26.658 | 34.977 / 35.362 | 0/0 | 1/1 |
| zero-local | 26.604 / 26.924 | 35.301 / 35.851 | 0/0 | 0/0 |
| baseline-final | 26.979 / 27.382 | 35.741 / 36.354 | 0/0 | 0/0 |
| selected | 26.486 / 26.837 | 35.237 / 35.790 | 0/0 | 0/0 |

## 1600: baseline-final → selected

| Kernel | Baseline ms | Selected ms | Regs | LMem B | SMem B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 0.976896 | 0.930816 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 0.605184 | 0.588800 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 0.681984 | 0.666624 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 1.619968 | 1.584128 | 225→226 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 0.577536 | 0.569344 | 225→226 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 0.994304 | 0.954368 | 167→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 1.016832 | 0.976896 | 167→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1.036288 | 1.015808 | 168→146 | 0→0 | 8192→10240 | 11→9 |
| c32_wave1_post_b8 | 4.051968 | 3.935232 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 5.050368 | 4.254720 | 151→153 | 0→0 | 10240→10240 | 9→9 |
| c32_wave1_up_b8 | 1.143808 | 1.117184 | 210→217 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 0.402432 | 0.398336 | 151→151 | 0→0 | 6144→6144 | 12→12 |
| c64_wave2_bi_bo_w16 | 0.663552 | 0.632832 | 234→241 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 0.816128 | 0.777216 | 241→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1.431552 | 0.773120 | 234→241 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 0.885760 | 0.863232 | 239→242 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w | 0.141312 | 0.141312 | 55→55 | 0→0 | 2176→2176 | 16→16 |
| decoder_project2x_h16w_w_bin_f8w16 | 0.068608 | 0.067584 | 47→47 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.165888 | 0.167936 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 0.089088 | 0.088064 | 33→33 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.045056 | 0.044032 | 62→62 | 0→0 | 2176→2176 | 32→32 |
| mh_pool_project_group_c256_f8w16 | 0.034816 | 0.035840 | 62→62 | 0→0 | 4224→4224 | 32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.035840 | 0.035840 | 62→62 | 0→0 | 8320→8320 | 32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.067584 | 0.066560 | 62→62 | 0→0 | 1152→1152 | 32→32 |
| split_ffn_one_w2f8_w16 | 0.439296 | 0.416768 | 186→106 | 0→0 | 0→0 | 8→16 |
| split_projection_frag_w16 | 0.160768 | 0.155648 | 119→119 | 0→0 | 1024→1024 | 16→16 |
| vit_attention_fused_640_bytein_bout | 0.705536 | 0.688128 | 119→119 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 0.816128 | 0.814080 | 80→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 0.036864 | 0.021504 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 0.950272 | 0.946176 | 106→106 | 0→0 | 4096→4096 | 16→16 |
| vit_stream_project_n64_bb_bout | 0.314368 | 0.283648 | 138→101 | 0→0 | 0→0 | 12→16 |
| vit_stream_qkv_frag_bin_w5f8 | 1.029120 | 1.013760 | 119→119 | 0→0 | 16384→16384 | 15→15 |

baseline: instrumented kernel total 25.687840 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

c32-only: instrumented kernel total 25.384960 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

layout-only: instrumented kernel total 25.156608 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

full: instrumented kernel total 25.189376 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

lowreg: instrumented kernel total 25.583616 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

zero-local: instrumented kernel total 25.097216 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

baseline-final: instrumented kernel total 27.055104 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

selected: instrumented kernel total 25.025536 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}`.

## 1920: baseline-final → selected

| Kernel | Baseline ms | Selected ms | Regs | LMem B | SMem B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 1.258496 | 1.219584 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 0.788480 | 0.770048 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 0.861184 | 0.842752 | 240→247 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 1.814528 | 1.772544 | 225→226 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 0.754688 | 0.738304 | 225→226 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1.329152 | 1.271808 | 167→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 1.359872 | 1.302528 | 167→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1.384448 | 1.363968 | 168→146 | 0→0 | 8192→10240 | 11→9 |
| c32_wave1_post_b8 | 5.466112 | 5.533696 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 5.877760 | 5.777408 | 151→153 | 0→0 | 10240→10240 | 9→9 |
| c32_wave1_up_b8 | 1.539072 | 1.497088 | 210→217 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 0.498688 | 0.503808 | 151→151 | 0→0 | 6144→6144 | 12→12 |
| c64_wave2_bi_bo_w16 | 0.891904 | 0.846848 | 234→241 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1.078272 | 1.029120 | 241→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1.080320 | 1.027072 | 234→241 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1.188864 | 1.146880 | 239→242 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 0.136192 | 0.135168 | 48→48 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.049152 | 0.048128 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4_bout | 0.139264 | 0.136192 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 0.116736 | 0.116736 | 33→33 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.054272 | 0.054272 | 62→62 | 0→0 | 2176→2176 | 32→32 |
| mh_pool_project_group_c256_out8_f8w16 | 0.043008 | 0.043008 | 62→62 | 0→0 | 4224→4224 | 32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.036864 | 0.036864 | 62→62 | 0→0 | 8320→8320 | 32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.080896 | 0.080896 | 62→62 | 0→0 | 1152→1152 | 32→32 |
| split_ffn_one_w2f8_w16_bin | 0.374784 | 0.342016 | 186→106 | 0→0 | 0→0 | 8→16 |
| split_projection_frag_w16_bskip | 0.164864 | 0.176128 | 119→119 | 0→0 | 1024→1024 | 16→16 |
| vit_attention_fused_640_bytein_bout | 1.255424 | 1.243136 | 119→119 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 1.114112 | 1.116160 | 80→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 0.024576 | 0.024576 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 1.213440 | 1.215488 | 106→106 | 0→0 | 4096→4096 | 16→16 |
| vit_stream_project_n64_bb_bout | 0.432128 | 0.362496 | 138→101 | 0→0 | 0→0 | 12→16 |
| vit_stream_qkv_frag_bin_w5f8 | 1.405952 | 1.406976 | 119→119 | 0→0 | 16384→16384 | 15→15 |

baseline: instrumented kernel total 33.750016 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

c32-only: instrumented kernel total 33.894400 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

layout-only: instrumented kernel total 33.842176 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

full: instrumented kernel total 34.962432 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

lowreg: instrumented kernel total 32.888832 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

zero-local: instrumented kernel total 33.030144 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

baseline-final: instrumented kernel total 33.813504 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

selected: instrumented kernel total 33.181696 ms. Baseline accuracy `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`; F32 visible `{"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}`.

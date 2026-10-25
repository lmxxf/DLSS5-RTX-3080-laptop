# Phase 6: IR alignment and native tensor transfers

Final comparisons: 50 warmup / 80 iterations; GPU events exclude initialization/transfers/readback. Separate instrumented frame for the kernel census.

| Resolution | Baseline min / median ms | Selected min / median ms | Speedup | PSNR vs F32 | Maxabs |
|---|---:|---:|---:|---:|---:|
| 1920×1080 | 49.145 / 49.394 | 36.538 / 36.891 | 1.3389× | 46.1009 dB | 0.04160273 |
| 1600×900 | 36.016 / 36.671 | 27.315 / 27.685 | 1.3246× | 46.9753 dB | 0.04004550 |

## Stage summary

baseline/aligned16/prefix-shared-q are final 50/80 runs; cap8/nobound pilots are 5/10 and half2 is 10/40. Selected aliases prefix-shared-q, not an independent repetition.

| Stage | 900p median ms | 1080p median ms |
|---|---:|---:|
| baseline | 36.671 | 49.394 |
| aligned16 | 27.666 | 36.798 |
| c32-cap8 | 27.448 | 36.563 |
| c32-nobound | 27.551 | 36.998 |
| c32-half2 | 27.551 | 36.498 |
| prefix-shared-q | 27.685 | 36.891 |
| selected | 27.685 | 36.891 |

## 1920×1080 (processing 1920×1152)

Bitdiff vs chosen Phase-3 baseline: 0; invalid=0; F32 metrics: `{"visible": {"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}, "padded": {"invalid": 0, "bitdiff": 6629656, "psnr_peak1_db": 46.08164586978773, "maxabs": 0.0416027307510376}}`

| Kernel | Calls before→after | Before ms | After ms | Regs | LMem | SMem | OccW |
|---|---:|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2→2 | 1.927168 | 1.298432 | 242→242 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 1→1 | 1.643520 | 0.811008 | 248→248 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 1→1 | 1.203200 | 0.883712 | 250→250 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 3→3 | 2.604032 | 1.816576 | 248→248 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 1→1 | 1.019904 | 0.757760 | 248→248 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1→1 | 1.368064 | 1.323008 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 1→1 | 1.425408 | 1.354752 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1→1 | 1.419264 | 1.406976 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_post_b8 | 1→1 | 5.720064 | 5.568512 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 1→1 | 6.328320 | 6.146048 | 168→152 | 0→0 | 8192→10240 | 11→9 |
| c32_wave1_up_b8 | 1→1 | 1.736704 | 1.605632 | 234→234 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 4→4 | 0.911360 | 0.574464 | 207→203 | 0→0 | 6144→6144 | 8→8 |
| c64_wave2_bi_bo_w16 | 1→1 | 1.224704 | 0.918528 | 242→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1→1 | 1.326080 | 1.101824 | 248→250 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1→1 | 1.413120 | 1.105920 | 242→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1→1 | 1.605632 | 1.223680 | 250→248 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2→2 | 0.363520 | 0.134144 | 61→48 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 1→1 | 0.132096 | 0.047104 | 138→89 | 0→0 | 0→0 | 12→16 |
| mh_attention_project_frag_c512_w16_u4_bout | 3→3 | 0.402432 | 0.140288 | 138→89 | 0→0 | 0→0 | 12→16 |
| mh_pool_project_c32_b8_out8 | 1→1 | 0.123904 | 0.115712 | 44→34 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1→1 | 0.076800 | 0.054272 | 110→62 | 0→0 | 2176→2176 | 16→32 |
| mh_pool_project_group_c256_out8_f8w16 | 1→1 | 0.076800 | 0.041984 | 110→62 | 0→0 | 4224→4224 | 16→32 |
| mh_pool_project_group_c512_out8_f8w16 | 1→1 | 0.066560 | 0.037888 | 110→62 | 0→0 | 8320→8320 | 16→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1→1 | 0.106496 | 0.079872 | 110→62 | 0→0 | 1152→1152 | 16→32 |
| split_ffn_one_w2f8_w16_bin | 4→4 | 0.796672 | 0.343040 | 164→106 | 0→0 | 0→0 | 12→16 |
| split_projection_frag_w16_bskip | 4→4 | 0.365568 | 0.156672 | 140→114 | 0→0 | 1024→1024 | 12→16 |
| vit_attention_fused_640_bytein_bout | 8→8 | 1.923072 | 1.200128 | 78→78 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8→8 | 2.833408 | 1.119232 | 120→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 2→2 | 0.029696 | 0.025600 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8→8 | 3.260416 | 1.207296 | 148→106 | 0→0 | 4096→4096 | 12→16 |
| vit_stream_project_n64_bb_bout | 8→8 | 1.336320 | 0.360448 | 150→101 | 0→0 | 0→0 | 12→16 |
| vit_stream_qkv_frag_bin_w5f8 | 8→8 | 3.733504 | 1.399808 | 119→119 | 0→0 | 16384→16384 | 15→15 |

Instrumented kernel total: 48.503808 → 34.360320 ms; active kernel kinds 32→32.

## 1600×900 (processing 1600×1024)

Bitdiff vs chosen Phase-3 baseline: 0; invalid=0; F32 metrics: `{"visible": {"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}, "padded": {"invalid": 0, "bitdiff": 4909833, "psnr_peak1_db": 46.95388561402703, "maxabs": 0.04004549980163574}}`

| Kernel | Calls before→after | Before ms | After ms | Regs | LMem | SMem | OccW |
|---|---:|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2→2 | 1.474560 | 0.995328 | 242→242 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 1→1 | 0.775168 | 0.619520 | 248→248 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 1→1 | 0.917504 | 0.697344 | 250→250 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 3→3 | 2.296832 | 1.626112 | 248→248 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 1→1 | 0.784384 | 0.581632 | 248→248 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1→1 | 1.005568 | 0.992256 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 1→1 | 1.067008 | 1.010688 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1→1 | 1.063936 | 1.052672 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_post_b8 | 1→1 | 4.169728 | 4.130816 | 167→167 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 1→1 | 4.679680 | 4.525024 | 168→152 | 0→0 | 8192→10240 | 11→9 |
| c32_wave1_up_b8 | 1→1 | 1.275904 | 1.201152 | 234→234 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 4→4 | 1.348608 | 0.460800 | 207→203 | 0→0 | 6144→6144 | 8→8 |
| c64_wave2_bi_bo_w16 | 1→1 | 0.919552 | 0.685056 | 242→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1→1 | 1.001472 | 0.831488 | 248→250 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1→1 | 1.045504 | 0.834560 | 242→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1→1 | 1.177600 | 0.924672 | 250→248 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w | 1→1 | 0.215040 | 0.144384 | 55→55 | 0→0 | 2176→2176 | 16→16 |
| decoder_project2x_h16w_w_bin_f8w16 | 1→1 | 0.152576 | 0.068608 | 61→47 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 4→4 | 0.446464 | 0.160768 | 138→89 | 0→0 | 0→0 | 12→16 |
| mh_pool_project_c32_b8_out8 | 1→1 | 0.094208 | 0.088064 | 44→34 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1→1 | 0.065536 | 0.045056 | 110→62 | 0→0 | 2176→2176 | 16→32 |
| mh_pool_project_group_c256_f8w16 | 1→1 | 0.068608 | 0.035840 | 110→62 | 0→0 | 4224→4224 | 16→32 |
| mh_pool_project_group_c512_out8_f8w16 | 1→1 | 0.066560 | 0.035840 | 110→62 | 0→0 | 8320→8320 | 16→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1→1 | 0.083968 | 0.066560 | 110→62 | 0→0 | 1152→1152 | 16→32 |
| split_ffn_one_w2f8_w16 | 4→4 | 0.691200 | 0.417792 | 164→106 | 0→0 | 0→0 | 12→16 |
| split_projection_frag_w16 | 4→4 | 0.313344 | 0.147456 | 140→110 | 0→0 | 1024→1024 | 12→16 |
| vit_attention_fused_640_bytein_bout | 8→8 | 1.071104 | 0.667648 | 78→78 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8→8 | 2.046976 | 0.813056 | 120→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 2→2 | 0.020480 | 0.020480 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8→8 | 2.167808 | 0.937984 | 148→106 | 0→0 | 4096→4096 | 12→16 |
| vit_stream_project_n64_bb_bout | 8→8 | 0.888832 | 0.287744 | 150→101 | 0→0 | 0→0 | 12→16 |
| vit_stream_qkv_frag_bin_w5f8 | 8→8 | 2.707456 | 1.014784 | 119→119 | 0→0 | 16384→16384 | 15→15 |

Instrumented kernel total: 36.103168 → 26.121184 ms; active kernel kinds 32→32.

# Phase 5: packed C/D Benes and register-Q controls

Final comparisons: 50 warmup / 80 iterations; GPU events exclude initialization/transfers/readback. Separate instrumented frame for the kernel census.

| Resolution | Baseline min / median ms | Selected min / median ms | Speedup | PSNR vs F32 | Maxabs |
|---|---:|---:|---:|---:|---:|
| 1920×1080 | 51.792 / 52.571 | 48.893 / 49.346 | 1.0654× | 46.1009 dB | 0.04160273 |
| 1600×900 | 38.604 / 39.105 | 36.095 / 36.671 | 1.0664× | 46.9753 dB | 0.04004550 |

## Stage summary

baseline/vector/vector-bound9/register-q-capped are final 50/80 runs; other Q variants are 10/40 pilots. Selected aliases the chosen run, not an independent repetition.

| Stage | 900p median ms | 1080p median ms |
|---|---:|---:|
| baseline | 39.105 | 52.571 |
| vector | 37.011 | 49.793 |
| vector-bound9 | 37.105 | 49.867 |
| register-q | 36.672 | 49.688 |
| register-q-uninit | 36.646 | 49.635 |
| register-q-bound9 | 36.658 | 49.659 |
| register-q-capped | 36.671 | 49.346 |
| selected | 36.671 | 49.346 |

## 1920×1080 (processing 1920×1152)

Bitdiff vs chosen Phase-3 baseline: 0; invalid=0; F32 metrics: `{"visible": {"invalid": 0, "bitdiff": 6215301, "psnr_peak1_db": 46.100947087035124, "maxabs": 0.0416027307510376}, "padded": {"invalid": 0, "bitdiff": 6629656, "psnr_peak1_db": 46.08164586978773, "maxabs": 0.0416027307510376}}`

| Kernel | Calls before→after | Before ms | After ms | Regs | LMem | SMem | OccW |
|---|---:|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2→2 | 2.052096 | 1.918976 | 250→242 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 1→1 | 1.080320 | 1.007616 | 250→248 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 1→1 | 1.265664 | 1.193984 | 250→250 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 3→3 | 2.727936 | 2.587648 | 250→248 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 1→1 | 1.124352 | 1.021952 | 250→248 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1→1 | 1.563648 | 1.355776 | 159→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_finish_dcrop_b8d | 1→1 | 1.634304 | 1.417216 | 159→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_mapped_b8 | 1→1 | 1.662976 | 1.419264 | 146→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_post_b8 | 1→1 | 6.592512 | 5.657600 | 160→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_prefix_b8d | 1→1 | 7.363584 | 6.339584 | 169→168 | 0→0 | 10240→8192 | 8→11 |
| c32_wave1_up_b8 | 1→1 | 1.915904 | 1.721344 | 234→234 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 4→4 | 0.946176 | 0.901120 | 229→207 | 0→0 | 6144→6144 | 8→8 |
| c64_wave2_bi_bo_w16 | 1→1 | 1.348608 | 1.223680 | 250→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1→1 | 1.446912 | 1.324032 | 250→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1→1 | 1.519616 | 1.399808 | 250→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1→1 | 1.701888 | 1.589248 | 250→250 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 2→2 | 0.360448 | 0.357376 | 61→61 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 1→1 | 0.132096 | 0.132096 | 140→138 | 0→0 | 0→0 | 12→12 |
| mh_attention_project_frag_c512_w16_u4_bout | 3→3 | 0.398336 | 0.396288 | 140→138 | 0→0 | 0→0 | 12→12 |
| mh_pool_project_c32_b8_out8 | 1→1 | 0.129024 | 0.123904 | 44→44 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1→1 | 0.077824 | 0.076800 | 111→110 | 0→0 | 2176→2176 | 16→16 |
| mh_pool_project_group_c256_out8_f8w16 | 1→1 | 0.075776 | 0.074752 | 111→110 | 0→0 | 4224→4224 | 16→16 |
| mh_pool_project_group_c512_out8_f8w16 | 1→1 | 0.067584 | 0.065536 | 111→110 | 0→0 | 8320→8320 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1→1 | 0.108544 | 0.105472 | 111→110 | 0→0 | 1152→1152 | 16→16 |
| split_ffn_one_w2f8_w16_bin | 4→4 | 0.794624 | 0.790528 | 152→164 | 0→0 | 0→0 | 12→12 |
| split_projection_frag_w16_bskip | 4→4 | 0.360448 | 0.357376 | 145→140 | 0→0 | 1024→1024 | 12→12 |
| vit_attention_fused_640_bytein_bout | 8→8 | 1.951744 | 1.923072 | 93→78 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8→8 | 2.857984 | 2.836480 | 121→120 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 2→2 | 0.024576 | 0.024576 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8→8 | 3.309568 | 3.270656 | 150→148 | 0→0 | 4096→4096 | 12→12 |
| vit_stream_project_n64_bb_bout | 8→8 | 1.356800 | 1.339392 | 155→150 | 0→0 | 0→0 | 12→12 |
| vit_stream_qkv_frag_bin_w5f8 | 8→8 | 3.806208 | 3.768320 | 119→119 | 0→0 | 16384→16384 | 15→15 |

Instrumented kernel total: 51.758080 → 47.721472 ms; active kernel kinds 32→32.

## 1600×900 (processing 1600×1024)

Bitdiff vs chosen Phase-3 baseline: 0; invalid=0; F32 metrics: `{"visible": {"invalid": 0, "bitdiff": 4315276, "psnr_peak1_db": 46.975322410562406, "maxabs": 0.04004549980163574}, "padded": {"invalid": 0, "bitdiff": 4909833, "psnr_peak1_db": 46.95388561402703, "maxabs": 0.04004549980163574}}`

| Kernel | Calls before→after | Before ms | After ms | Regs | LMem | SMem | OccW |
|---|---:|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 2→2 | 1.584128 | 1.474560 | 250→242 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 1→1 | 0.823296 | 0.776192 | 250→248 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 1→1 | 0.986112 | 0.913408 | 250→250 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 3→3 | 2.430976 | 2.294784 | 250→248 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 1→1 | 0.855040 | 0.790528 | 250→248 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1→1 | 1.159168 | 1.018880 | 159→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_finish_dcrop_b8d | 1→1 | 1.226752 | 1.060864 | 159→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_mapped_b8 | 1→1 | 1.236992 | 1.063936 | 146→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_post_b8 | 1→1 | 4.899840 | 4.210688 | 160→167 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_prefix_b8d | 1→1 | 5.452800 | 4.695040 | 169→168 | 0→0 | 10240→8192 | 8→11 |
| c32_wave1_up_b8 | 1→1 | 1.418240 | 1.290240 | 234→234 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 4→4 | 0.754688 | 0.722944 | 229→207 | 0→0 | 6144→6144 | 8→8 |
| c64_wave2_bi_bo_w16 | 1→1 | 1.008640 | 0.918528 | 250→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1→1 | 1.091584 | 0.997376 | 250→248 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1→1 | 1.137664 | 1.052672 | 250→242 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1→1 | 1.278976 | 1.176576 | 250→250 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w | 1→1 | 0.216064 | 0.209920 | 55→55 | 0→0 | 2176→2176 | 16→16 |
| decoder_project2x_h16w_w_bin_f8w16 | 1→1 | 0.153600 | 0.153600 | 61→61 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 4→4 | 0.449536 | 0.450560 | 140→138 | 0→0 | 0→0 | 12→12 |
| mh_pool_project_c32_b8_out8 | 1→1 | 0.097280 | 0.093184 | 44→44 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 1→1 | 0.064512 | 0.064512 | 111→110 | 0→0 | 2176→2176 | 16→16 |
| mh_pool_project_group_c256_f8w16 | 1→1 | 0.070656 | 0.076800 | 111→110 | 0→0 | 4224→4224 | 16→16 |
| mh_pool_project_group_c512_out8_f8w16 | 1→1 | 0.065536 | 0.064512 | 111→110 | 0→0 | 8320→8320 | 16→16 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 1→1 | 0.086016 | 0.084992 | 111→110 | 0→0 | 1152→1152 | 16→16 |
| split_ffn_one_w2f8_w16 | 4→4 | 0.675840 | 0.684032 | 152→164 | 0→0 | 0→0 | 12→12 |
| split_projection_frag_w16 | 4→4 | 0.317440 | 0.315392 | 145→140 | 0→0 | 1024→1024 | 12→12 |
| vit_attention_fused_640_bytein_bout | 8→8 | 1.094656 | 1.071104 | 93→78 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 8→8 | 2.049024 | 2.039808 | 121→120 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 2→2 | 0.020480 | 0.020480 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 8→8 | 2.158592 | 2.163712 | 150→148 | 0→0 | 4096→4096 | 12→12 |
| vit_stream_project_n64_bb_bout | 8→8 | 0.890880 | 0.886784 | 155→150 | 0→0 | 0→0 | 12→12 |
| vit_stream_qkv_frag_bin_w5f8 | 8→8 | 2.701312 | 2.697216 | 119→119 | 0→0 | 16384→16384 | 15→15 |

Instrumented kernel total: 38.456320 → 35.533824 ms; active kernel kinds 32→32.

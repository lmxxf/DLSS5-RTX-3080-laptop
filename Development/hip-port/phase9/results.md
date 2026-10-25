# Phase 9: Graph, V bridge, register-Q

50 warmup / 80 iter; padded processing 1600×1024 / 1920×1152. PROFILE_TOTAL is a separate instrumented frame, not the GPU median frame. Graph runs skip instrumentation; compare their GPU/Wall distributions directly.

| Variant | 900p GPU min / median | 900p Wall median | 1080p GPU min / median | 1080p Wall median | LMem kernels 900/1080 |
|---|---:|---:|---:|---:|---:|
| baseline | 26.169 / 26.637 | 26.728 | 35.026 / 35.361 | 35.446 | 0/0 |
| graph-only | 26.324 / 26.675 | 26.801 | 34.948 / 35.536 | 35.655 | not profiled/not profiled |
| v-bridge | 26.119 / 26.546 | 26.669 | 34.837 / 35.244 | 35.345 | 0/0 |
| v-graph | 26.267 / 26.545 | 26.697 | 34.797 / 35.376 | 35.524 | not profiled/not profiled |
| q63-lowreg | 26.018 / 26.283 | 26.380 | 34.416 / 35.028 | 35.104 | 1/1 |
| q63-graph | 25.841 / 26.282 | 26.387 | 34.512 / 35.081 | 35.203 | not profiled/not profiled |
| q63-peel | 26.880 / 27.180 | 27.287 | 35.522 / 36.139 | 36.258 | 1/1 |
| q63-peel-graph | 26.835 / 27.206 | 27.326 | 35.862 / 36.348 | 36.479 | not profiled/not profiled |
| q63-fast | 25.964 / 26.363 | 26.484 | 34.503 / 35.112 | 35.211 | 1/1 |
| q31-lowreg | 26.097 / 26.446 | 26.586 | 34.601 / 35.103 | 35.200 | 0/0 |
| q63-policy | 25.974 / 26.445 | 26.543 | 34.542 / 35.160 | 35.250 | 0/0 |
| q63-policy-graph | 26.122 / 26.501 | 26.599 | 34.884 / 35.250 | 35.370 | not profiled/not profiled |
| baseline-final | 26.369 / 26.641 | 26.720 | 34.954 / 35.486 | 35.618 | 0/0 |
| selected | 26.265 / 26.612 | 26.722 | 34.924 / 35.318 | 35.407 | 0/0 |
| selected-graph | 26.254 / 26.614 | 26.727 | 35.058 / 35.420 | 35.555 | not profiled/not profiled |

## 1600: baseline-final → selected (Graph off)

| Kernel | Before ms | After ms | Regs | LMem B | SMem B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 0.929792 | 0.923648 | 247→231 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 0.587776 | 0.586752 | 247→231 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 0.666624 | 0.660480 | 247→232 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 1.596416 | 1.583104 | 226→226 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 0.566272 | 0.567296 | 226→226 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 0.954368 | 0.949248 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 0.975872 | 0.986112 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1.015808 | 0.979968 | 146→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_post_b8 | 3.936256 | 3.910656 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 4.281344 | 4.120576 | 153→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_up_b8 | 1.116160 | 1.111040 | 217→217 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 0.399360 | 0.401408 | 151→151 | 0→0 | 6144→6144 | 12→12 |
| c64_wave2_bi_bo_w16 | 0.631808 | 0.626688 | 241→225 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 0.777216 | 0.772096 | 242→226 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 0.772096 | 0.771072 | 241→225 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 0.865280 | 0.861184 | 242→231 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w | 0.142336 | 0.141312 | 55→55 | 0→0 | 2176→2176 | 16→16 |
| decoder_project2x_h16w_w_bin_f8w16 | 0.068608 | 0.068608 | 47→47 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.178176 | 0.166912 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 0.087040 | 0.088064 | 33→33 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.045056 | 0.045056 | 62→62 | 0→0 | 2176→2176 | 32→32 |
| mh_pool_project_group_c256_f8w16 | 0.034816 | 0.035840 | 62→62 | 0→0 | 4224→4224 | 32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.034816 | 0.035840 | 62→62 | 0→0 | 8320→8320 | 32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.067584 | 0.066560 | 62→62 | 0→0 | 1152→1152 | 32→32 |
| split_ffn_one_w2f8_w16 | 0.416768 | 0.417792 | 106→106 | 0→0 | 0→0 | 16→16 |
| split_projection_frag_w16 | 0.153600 | 0.156672 | 119→119 | 0→0 | 1024→1024 | 16→16 |
| vit_attention_fused_640_bytein_bout | 0.689152 | 0.696320 | 119→119 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 0.809984 | 0.818176 | 80→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 0.019456 | 0.020480 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 0.957440 | 0.954368 | 106→106 | 0→0 | 4096→4096 | 16→16 |
| vit_stream_project_n64_bb_bout | 0.288768 | 0.291840 | 101→101 | 0→0 | 0→0 | 16→16 |
| vit_stream_qkv_frag_bin_w5f8 | 1.014784 | 1.021952 | 119→119 | 0→0 | 16384→16384 | 15→15 |

baseline: kernel total `25.067519999999995` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

graph-only: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

v-bridge: kernel total `24.9416` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

v-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-lowreg: kernel total `25.72185600000001` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-peel: kernel total `25.561087999999998` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-peel-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-fast: kernel total `24.787968` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q31-lowreg: kernel total `24.763391999999996` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-policy: kernel total `25.340992` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-policy-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

baseline-final: kernel total `25.080832` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

selected: kernel total `24.83712` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

selected-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

## 1920: baseline-final → selected (Graph off)

| Kernel | Before ms | After ms | Regs | LMem B | SMem B | OccW |
|---|---:|---:|---:|---:|---:|---:|
| c128_wave2_bi_bo_w16 | 1.219584 | 1.213440 | 247→231 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_bi_ho | 1.409024 | 0.761888 | 247→231 | 0→0 | 24576→24576 | 8→8 |
| c128_wave2_up_lb_sh | 0.846848 | 0.846848 | 247→232 | 0→0 | 24576→24576 | 8→8 |
| c256_wave2_bi_bo_w16 | 1.770496 | 1.767424 | 226→226 | 0→0 | 49152→49152 | 8→8 |
| c256_wave2_bi_w16 | 0.739328 | 0.739328 | 226→226 | 0→0 | 49152→49152 | 8→8 |
| c32_wave1_finish_b8 | 1.363968 | 1.264640 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_finish_dcrop_b8d | 1.304576 | 1.297408 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_mapped_b8 | 1.359872 | 1.314816 | 146→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_post_b8 | 5.690368 | 5.268480 | 168→168 | 0→0 | 8192→8192 | 11→11 |
| c32_wave1_prefix_b8d | 5.783552 | 5.561056 | 153→168 | 0→0 | 10240→8192 | 9→11 |
| c32_wave1_up_b8 | 1.581056 | 1.489920 | 217→217 | 0→0 | 10240→10240 | 8→8 |
| c512_qkv_attention_compact_w16 | 0.495616 | 0.496640 | 151→151 | 0→0 | 6144→6144 | 12→12 |
| c64_wave2_bi_bo_w16 | 0.846848 | 0.839680 | 241→225 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_ho | 1.031168 | 1.020928 | 242→226 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_bi_w16 | 1.022976 | 1.019904 | 241→225 | 0→0 | 12288→12288 | 8→8 |
| c64_wave2_up_lb_sh | 1.156096 | 1.141760 | 242→231 | 0→0 | 12288→12288 | 8→8 |
| decoder_project2x_h16w_byteout_w_bin_f8w16 | 0.138240 | 0.135168 | 48→48 | 0→0 | 2176→2176 | 16→16 |
| mh_attention_project_frag_c512_w16_u4 | 0.048128 | 0.049152 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_attention_project_frag_c512_w16_u4_bout | 0.135168 | 0.137216 | 120→120 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_c32_b8_out8 | 0.116736 | 0.116736 | 33→33 | 0→0 | 0→0 | 16→16 |
| mh_pool_project_group_c128_hin_out8_f8w16 | 0.054272 | 0.054272 | 62→62 | 0→0 | 2176→2176 | 32→32 |
| mh_pool_project_group_c256_out8_f8w16 | 0.043008 | 0.043008 | 62→62 | 0→0 | 4224→4224 | 32→32 |
| mh_pool_project_group_c512_out8_f8w16 | 0.036864 | 0.037888 | 62→62 | 0→0 | 8320→8320 | 32→32 |
| mh_pool_project_group_c64_hin_out8_f8w16 | 0.080896 | 0.080896 | 62→62 | 0→0 | 1152→1152 | 32→32 |
| split_ffn_one_w2f8_w16_bin | 0.340992 | 0.342016 | 106→106 | 0→0 | 0→0 | 16→16 |
| split_projection_frag_w16_bskip | 0.162848 | 0.164864 | 119→119 | 0→0 | 1024→1024 | 16→16 |
| vit_attention_fused_640_bytein_bout | 1.243136 | 1.250304 | 119→119 | 0→0 | 0→0 | 16→16 |
| vit_expand_blocked_fp8_frag_bytein_w16 | 1.130496 | 1.114112 | 80→80 | 0→0 | 0→0 | 16→16 |
| vit_gather_b8 | 0.025600 | 0.025600 | 16→16 | 0→0 | 0→0 | 48→48 |
| vit_stream_contract_frag_bstream_bout | 1.217536 | 1.209344 | 106→106 | 0→0 | 4096→4096 | 16→16 |
| vit_stream_project_n64_bb_bout | 0.358400 | 0.360448 | 101→101 | 0→0 | 0→0 | 16→16 |
| vit_stream_qkv_frag_bin_w5f8 | 1.410048 | 1.411072 | 119→119 | 0→0 | 16384→16384 | 15→15 |

baseline: kernel total `32.922624` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

graph-only: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

v-bridge: kernel total `33.364000000000004` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

v-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-lowreg: kernel total `32.330752` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-peel: kernel total `33.616927999999994` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-peel-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-fast: kernel total `34.174975999999994` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q31-lowreg: kernel total `32.56425599999999` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-policy: kernel total `33.002495999999994` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

q63-policy-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

baseline-final: kernel total `34.16374400000001` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

selected: kernel total `32.57625600000001` ms, launches `83`, graph `{"enabled": 0, "builds": 0, "replays": 0, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

selected-graph: kernel total `None` ms, launches `None`, graph `{"enabled": 1, "builds": 1, "replays": 130, "small": 1, "wave_owned": 1, "final_direct": 1}`, baseline bitdiff/invalid `{"invalid": 0, "bitdiff": 0, "psnr_peak1_db": 999.0, "maxabs": 0.0}`.

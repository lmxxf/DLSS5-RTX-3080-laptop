# ABBA summary

Each row averages two run medians only for a compact comparison; raw min/median/wall/profile stay paired in results.md. Default DVFS; no equal-clock causal claim.

| Round | Width | A1 | B1 | B2 | A2 | Mean median change B-A ms |
|---|---:|---:|---:|---:|---:|---:|
| tail-abba | 1280 | 14.102 | 14.087 | 14.083 | 14.146 | -0.0390 |
| tail-abba | 1600 | 23.628 | 24.193 | 23.712 | 24.309 | -0.0160 |
| tail-abba | 1920 | 32.091 | 31.915 | 32.402 | 32.326 | -0.0500 |
| confirm-abba | 1280 | 14.173 | 14.444 | 14.432 | 14.899 | -0.0980 |
| confirm-abba | 1600 | 25.241 | 24.444 | 24.437 | 24.518 | -0.4390 |
| confirm-abba | 1920 | 32.538 | 32.606 | 32.463 | 32.592 | -0.0305 |

## Four ViT kernels, independent instrumented frames

| Round | Width | Kernel | A1 | B1 | B2 | A2 |
|---|---:|---|---:|---:|---:|---:|
| tail-abba | 1280 | vit_expand_blocked_fp8_frag_bytein_w16 | 0.512032 | 0.495616 | 0.478208 | 0.494592 |
| tail-abba | 1280 | vit_stream_contract_frag_bstream_bout | 0.677888 | 0.654336 | 0.649216 | 0.662528 |
| tail-abba | 1280 | vit_stream_project_n64_bb_bout | 0.207872 | 0.224256 | 0.209920 | 0.211968 |
| tail-abba | 1280 | vit_stream_qkv_frag_bin_w5f8 | 0.559104 | 0.582656 | 0.560128 | 0.568320 |
| tail-abba | 1600 | vit_expand_blocked_fp8_frag_bytein_w16 | 0.796672 | 0.796672 | 0.807936 | 0.798720 |
| tail-abba | 1600 | vit_stream_contract_frag_bstream_bout | 0.941056 | 0.944128 | 0.941056 | 0.942080 |
| tail-abba | 1600 | vit_stream_project_n64_bb_bout | 0.281600 | 0.280576 | 0.281600 | 0.281600 |
| tail-abba | 1600 | vit_stream_qkv_frag_bin_w5f8 | 1.002496 | 1.003520 | 1.005568 | 1.001472 |
| tail-abba | 1920 | vit_expand_blocked_fp8_frag_bytein_w16 | 1.434624 | 1.088512 | 1.087488 | 1.097728 |
| tail-abba | 1920 | vit_stream_contract_frag_bstream_bout | 1.692672 | 1.208320 | 1.299456 | 1.211392 |
| tail-abba | 1920 | vit_stream_project_n64_bb_bout | 0.355328 | 0.356352 | 0.354304 | 0.357376 |
| tail-abba | 1920 | vit_stream_qkv_frag_bin_w5f8 | 1.391616 | 1.397760 | 1.392640 | 1.385472 |
| confirm-abba | 1280 | vit_expand_blocked_fp8_frag_bytein_w16 | 0.490496 | 0.479232 | 0.667648 | 0.494592 |
| confirm-abba | 1280 | vit_stream_contract_frag_bstream_bout | 0.686080 | 0.649216 | 0.868352 | 0.662528 |
| confirm-abba | 1280 | vit_stream_project_n64_bb_bout | 0.208896 | 0.206848 | 0.472064 | 0.222208 |
| confirm-abba | 1280 | vit_stream_qkv_frag_bin_w5f8 | 0.557056 | 0.559104 | 0.565248 | 0.560128 |
| confirm-abba | 1600 | vit_expand_blocked_fp8_frag_bytein_w16 | 0.798720 | 0.800768 | 0.798720 | 0.800768 |
| confirm-abba | 1600 | vit_stream_contract_frag_bstream_bout | 0.945152 | 0.941056 | 0.937984 | 0.945152 |
| confirm-abba | 1600 | vit_stream_project_n64_bb_bout | 0.283648 | 0.282624 | 0.284672 | 0.280576 |
| confirm-abba | 1600 | vit_stream_qkv_frag_bin_w5f8 | 1.008640 | 1.004544 | 1.007616 | 1.010688 |
| confirm-abba | 1920 | vit_expand_blocked_fp8_frag_bytein_w16 | 1.101824 | 1.097728 | 1.087488 | 1.389568 |
| confirm-abba | 1920 | vit_stream_contract_frag_bstream_bout | 1.212416 | 1.201152 | 1.198080 | 1.217536 |
| confirm-abba | 1920 | vit_stream_project_n64_bb_bout | 0.352256 | 0.355328 | 0.355328 | 0.366592 |
| confirm-abba | 1920 | vit_stream_qkv_frag_bin_w5f8 | 1.388544 | 1.395712 | 1.384448 | 1.406976 |

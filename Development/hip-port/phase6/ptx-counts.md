# PTX memory instruction census

Static counts include all entry points and helpers, not per-frame dynamic execution. Word vectors are v2/v4 of 32-bit elements.

| Module | Scalar u8 before→after | Word v2 before→after | Word v4 before→after |
|---|---:|---:|---:|
| boundary-fast | 2→2 | 0→0 | 0→0 |
| boundary_reference | 0→0 | 0→0 | 0→0 |
| c32-wave1-fast-norm900 | 15970→7282 | 936→1650 | 626→848 |
| c32-wave1-fast | 15970→7282 | 808→1538 | 626→848 |
| c32-wave1-rtz | 15970→7282 | 936→1650 | 626→848 |
| c32-wave1 | 15970→7282 | 936→1650 | 626→848 |
| c32_fast | 0→0 | 0→0 | 0→0 |
| c32_fast_attention | 0→0 | 0→0 | 0→0 |
| c32_fused_attention | 224→224 | 0→0 | 0→0 |
| c32_fused_ffn_attention-packed | 10400→6256 | 0→346 | 0→18 |
| c32_fused_ffn_attention | 6432→6256 | 0→0 | 0→18 |
| c32_prefix_reference | 0→0 | 0→0 | 0→0 |
| c32_tiled | 0→0 | 0→0 | 0→0 |
| c32_wmma | 0→0 | 0→0 | 0→0 |
| c512-m32-deep | 8691→2355 | 4→196 | 28→259 |
| c512-m32-mh | 18044→5156 | 0→1000 | 32→252 |
| c64-wave2-fast | 34172→5060 | 0→2515 | 24→342 |
| c64-wave2 | 34172→5060 | 0→2515 | 24→342 |
| deep_fast-packed-fast | 7147→2131 | 5→197 | 359→536 |
| deep_fast-packed | 7147→2131 | 5→197 | 359→536 |
| deep_fast | 6771→2131 | 4→184 | 24→175 |
| deep_reference | 0→0 | 0→0 | 0→0 |
| deep_wmma | 0→0 | 0→0 | 0→0 |
| multi-pass-predict | 0→0 | 0→0 | 0→0 |
| multi-pass-skin | 0→0 | 0→0 | 0→0 |
| multihead-fast-packed | 0→0 | 0→0 | 0→0 |
| multihead-fast-padded-wave-packed | 18304→5824 | 0→777 | 24→298 |
| multihead-fast-padded-wave | 15672→5944 | 0→769 | 24→238 |
| multihead-fast | 0→0 | 0→0 | 0→0 |
| multihead-reference | 0→0 | 0→0 | 0→0 |
| multihead-tiled | 0→0 | 0→0 | 0→0 |
| multihead-wmma | 0→0 | 0→0 | 0→0 |
| multihead_fused_attention | 7953→2009 | 0→498 | 0→0 |
| prefix_fast | 0→0 | 0→0 | 0→0 |
| swin-persistent-fast | 16108→4900 | 0→945 | 24→238 |
| swin-persistent | 16108→4900 | 0→945 | 24→238 |
| vit-stream-fast | 9267→2643 | 4→342 | 44→279 |
| vit-stream | 9267→2643 | 4→342 | 44→279 |
| vit-wide-deep | 6899→2131 | 4→200 | 24→175 |
| wave-pointwise | 0→0 | 0→0 | 0→0 |

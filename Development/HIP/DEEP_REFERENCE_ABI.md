# Split C512 / ViT SDKless reference ABI

`deep_reference.hip` is a standalone scalar GPU numerical reference, **not a performance backend**. No SDK headers/device library. Launch every symbol with block `(256,1,1)`, grid `(ceil(N/256),1,1)`, no shared memory. All dimensions `uint32_t`, buffers device pointers; float tensors/weights are f32 carrying the original H/F-rounded values. Weights use original shader offsets (in float elements), not WMMA layouts. No buffer aliasing; launch dependent stages on the same stream or synchronize explicitly. Host validates counts and overflow before launch.

Signatures (argument order exactly as listed):

| Kernel | Arguments | N |
|---|---|---|
| split_mix | input, weights, mixed, tokens | tokens*512 |
| split_expand | mixed, weights, hidden, tokens | tokens*2048 |
| split_contract | hidden, weights, output, tokens | tokens*512 |
| split_projection | input, weights, residual, output, tokens | tokens*512 |
| vit_qkv_project | input, weights, output, tokens | tokens*3072 |
| vit_qkv_normalize | input, weights, output, tokens | tokens*96 |
| vit_attention_scores[_fast] | qkv, ex, tokens | tokens*32*tokens |
| vit_attention_inverse[_fast] | ex, inverse, tokens | tokens*32 |
| vit_attention_av[_fast] | qkv, ex, inverse, output, tokens | tokens*1024 |
| vit_expand | input, weights, output, tokens, input_channels, output_channels | tokens*output_channels |
| vit_project | input, weights, residual, output, tokens, input_channels, output_channels | tokens*output_channels |
| decoder_project2x | input, weights, residual, output, input_width, input_height, output_width, output_height, input_channels, output_channels | input_width*input_height*output_channels |
| vit_gather | input, indices, output, count | count |

Only indices is `const uint32_t*`; other buffers are float pointers. Inputs const, final result pointer writable. `tokens = width*height` for split. Split stages use mixed `[token][512]`, hidden `[token][8][256]`; split projection uses its own projection weight blob, not split FFN weights.

ViT QKV is `[part Q/K/V][token][1024]`. Normalization preserves original tensor_channel permutation, half-square midpoint correction and exact reduction tree. Q scales use original `weights[3145728+head]`. `ex` is `[query][head32][key]`, inverse `[query][head32]`. QKV project produces H, normalization F, attention output F(H).

**Attention modes are not interchangeable.** Legacy names without `_fast` reproduce `native_vit_attention.hlsl`: half-rounded score, custom half-bit exponent approximation, original half denominator tree/key permutation, half inverse, half accumulation every 32 keys. Host must require `tokens % 64 == 0`; do not silently pad with valid keys. Fast names correspond to production `native_wave_vit_attention_fp8.hlsl`: no H(score), F32 denominator/inverse/AV accumulation, same custom exponent bit map and F(ex) numerator. These accept 240/400/640 tokens directly and omit masked tail keys. Scalar F32 summation order may differ from WMMA, so cross-backend bit equality is not promised. Neither path is ordinary softmax.

All matrix channels divisible by 32; `vit_project` additionally requires input_channels divisible by 128 (four separately H-accumulated partitions). Decoder input_channels==1024 uses four partitions, others one. Decoder emits clipped nearest 2x copies and merges F(residual)*scale at `weights[input_channels*output_channels+row]`; C32 result stays H, larger channels F. Explicit dimensions replace original token-count lookup and support the padded bottleneck crop (e.g. 32x20 -> 60x36). Output extents must be <=2*input extents; residual/output match output extents. Never infer a square from token count.

Gather indices are supplied by host's existing `NativeVitLogicalMap`/decoder mapping; no reshape assumptions. Validate every index before upload.

Sources checked: `native_split.hlsl`, `native_vit_qkv.hlsl`, `native_half_square.hlsli`, `native_vit_attention.hlsl`, `native_wave_vit_attention_fp8.hlsl`, `native_vit_linear.hlsl`, `native_vit_gather.hlsl`.

Validation: COMGR 3.0 / Clang21 gfx1201 compilation (no GPU launch). Numerical GPU parity remains to be measured. Contract/reassociation disabled; H/F finite-input helpers match the shared scalar reference (nonfinite F behavior is not an oracle for HLSL).

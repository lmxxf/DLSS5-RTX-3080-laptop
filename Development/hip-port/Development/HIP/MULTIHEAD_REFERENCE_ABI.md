# Multihead reference ABI

`multihead_reference.hip` is a **scalar GPU numerical reference**, not the HIP performance backend. It follows the non-wave branches of `shaders/native_c64.hlsl`, `native_c64_shift.hlsl` and `native_c64_ds.hlsl`. GEMMs are scalar 32-product loops with the original H() boundaries; later WMMA replacement should be checked against saved intermediate buffers. The full HIP/HLSL FP8 WMMA baseline is documented separately in `wmma_probe.md`.

## Compilation and execution contract

No HIP SDK headers or device libraries. COMGR3/Clang21 compiled this source for gfx1201 into a111,112-byte code object on2026-09-14, with wave32 metadata. `readelf -Ws` found no named undefined symbols. All14 stage entry points are present. That size records the initial C64/128/256 build; the extended guards require rebuilding. This compilation did not execute GPU kernels. Device execution and comparison against HLSL are still pending.

Remote artifacts: `D:\DLSSNR-Lab\hip-backend\multihead-reference.hsaco` and `.hsaco.s`; read-only copies are in gitignored `release/HIP/`. Build through the existing `rtc_compile.exe OUTPUT SOURCE comgr` three-stage path. Source disables floating-point contraction/reassociation. Backend FMA used to implement floating-point division is expected and does not mean the dot loops were silently contracted.

Every kernel uses grid `(ceil(work_items/256),1,1)`, block **`(256,1,1)`**, shared memory0. A256-thread block contains eight32-lane waves; it does not imply a256-lane wave. All pointers are float32 device buffers. All scalar arguments are unsigned32-bit values. `channels` is a runtime argument: FFN accepts64/128/256; QKV/norm/ex/prob/AV/attention projection and split projection additionally accept512; shift pack/crop and pool/pool projection accept32/64/128/256/512. These are separate guards: accepting C32 for spatial operations does not enable C32 multihead FFN. A single module exports all supported variants. `tokens=width*height`, `heads=channels/32`, `windows=(width/8)*(height/8)`.

The host must validate positive dimensions, valid channel count, input/output allocation sizes,32-bit index bounds, and dispatch bounds. Attention requires width and height divisible by8; perform pack first for other geometries. An invalid channel count causes no writes, so output sentinels must be checked rather than interpreted as success. Sources/destinations cannot alias unless separately demonstrated safe. Synchronize or order kernels on one stream before consuming intermediate buffers.

## Stage signatures

Names below denote device pointers unless explicitly a scalar. The listed work-item count controls the grid.

| Export | Arguments in exact order | Work items | Output layout |
|---|---|---:|---|
| `mh_ffn_expand` | input, weights, hidden, tokens, channels | tokens×4C | hidden[p][4C] |
| `mh_ffn_contract` | hidden, weights, middle, tokens, channels | tokens×C | middle[p][C] |
| `mh_ffn_project` | middle, feature, weights, output, tokens, channels | tokens×C | output[p][C] |
| `mh_qkv` | input, weights, qkv, tokens, channels | tokens×3C | qkv[p][Q,K,V][C] |
| `mh_normalize` | qkv, weights, qk, tokens, channels | tokens×heads | qk[p][Q,K][C] |
| `mh_scores_exp` | qk, weights, ex, width, height, channels | windows×heads×4096 | ex[window][head][query64][key64] |
| `mh_probabilities` | ex, prob, windows, channels | windows×heads×64 | prob same layout as ex |
| `mh_attention_av` | prob, qkv, av, width, height, channels | tokens×C | av[p][C] |
| `mh_attention_project` | av, feature, weights, output, tokens, channels, raw_output | tokens×C | output[p][C] |
| `mh_split_project` | input, feature, weights, output, tokens, channels | tokens×C | output[p][C] |
| `mh_shift_pack` | input, output, width, height, work_width, work_height, pad_x, pad_y, channels, plain_short_y | work_width×work_height×C | padded raster HWC |
| `mh_shift_crop` | input, output, width, height, work_width, pad_x, pad_y, channels | width×height×C | cropped raster HWC |
| `mh_pool` | raw, pooled, width, height, source_width, valid_width, valid_height, channels | width×height×C | pooled[p][C] |
| `mh_pool_project` | pooled, weights, output, width, height, valid_width, valid_height, channels | width×height×2C | output[p][2C] |

`C` in the table means channels. `feature` is the residual/skip source, not the intermediate middle/AV input. `raw_output=1` keeps the final H() result of attention projection, matching `RAW_OUTPUT`; zero additionally applies F(). FFN and split projections always apply F().

All activation layouts are **raster HWC**, except explicitly listed per-window ex/prob scratch arrays. QKV is interleaved by pixel then part, matching `NATIVE_PRECOMPUTED_QKV` in the original multihead shader. It is not the C32 module's part-major layout. Raw Q,K,V each retain H() output; V is F()-quantized when consumed by AV. Norm output has two parts, not three.

## Original weight buffers

Offsets and lengths are float32 **elements**, not bytes. No repacking, transposition or biases are introduced.

| Buffer | Locations | Minimum elements |
|---|---|---:|
| FFN | expand[4C][C] at0; contract[C][4C] at4C²; project[C][C] at8C²; residual[C] at9C² | 9C²+C |
| Attention | Q/K/V[C][C] at0/C²/2C²; projection[C][C] at3C²; bias[head][query64][key64] at4C²; scale[head] at4C²+heads×4096; residual[C] immediately after scale | 4C²+heads×4096+heads+C |
| Split projection | matrix[C][C] at0; residual[C] atC² | C²+C |
| Pool projection | matrix[2C][C] at0 | 2C² |

Weight indexing is `[output_row][input_channel]`; activations are `[pixel][channel]`. Attention weights are independent of the number of spatial windows; each window reuses the same head bias table.

## Numerical details retained

- Every32-channel dot group is accumulated in FP32, then H(previous+group_sum); skip contribution enters **before** those groups. This is not equivalent to adding skip after a complete GEMM.
- FFN gate uses the original constants −0.055908203125,0.447265625,0.89453125 with the same nested H() and F() placements.
- Normalization uses `NativeHalfSquarePair`'s recovered sum residual, followed by the original16→8 adjacent-pair reduction then8→4→2→1 split-half tree. Minimum norm is6.198883056640625e-5. Reciprocal square root uses AMD's native builtin followed by H(); this instruction still needs direct HLSL comparison.
- Approximate exponent is the original **half-bit transform**: H(score×0.044921875+1.30078125), clamp[1.03125,1.5693359375], half bits shifted5 then add0x8000 and keep16 bits. There is no ordinary exp, max-score subtraction or generic softmax.
- Probability denominator retains both parity groups and the original four-lane ordering of half additions. Reciprocal is H(1/H(total)). LLVM division lowering may differ from the HLSL reciprocal at edge cases, so ex and prob are independent comparison boundaries.
- AV has two32-key groups, H() after each; Q/K dots, AV and other scalar GEMMs are deliberately not claimed bit-identical to the wave-matrix reduction order before GPU testing.
- F() uses the bit-based finite E4M3 round-to-nearest-even/saturating conversion matching `native_fp8_fast.hlsli` on its validated finite-half domain. H() preserves input NaN/Inf bits as in the source helper. The reference contract is finite activations/weights and finite values at F() calls; nonfinite LegacyF/log2 behavior is not established here and must not be silently used as validation success.

## Shift and pooling geometry

`mh_shift_pack` subtracts pad_x/pad_y from each work coordinate and **zero-fills** outside the source rectangle. It is not generic cyclic shifting. `plain_short_y=1` enables precisely the original special case channels256 and source height4, wrapping y modulo4; no other coordinate wraps. Crop adds pad_x/pad_y, and the host must ensure the resulting source rectangle fits the work buffer.

Pool width/height are the **pooled output** dimensions, whereas source_width is the raw input row pitch. The host ensures every valid output has a full2×2 source cell. Top and bottom pairs each round through H(), followed by H(top+bottom), multiply¼,H(),F(). Optional valid rectangle behavior matches the shader: valid_width0 disables the mask; otherwise cells with x>=valid_width or y>=valid_height are explicitly zeroed before raw loads. Pool projection reapplies the mask and computes2C output channels with the original grouped H() sums. This allows C256→C512 downsample without adding a C512 attention implementation.

## Suggested first differential run

Run C64/C128/C256 independently on8×8 and16×8 finite fixtures, initially low magnitudes to avoid half overflow. Save each stage: expand→contract→FFN projection; rawQKV→normalizedQK→ex→prob→AV→attention projection with raw on/off. Check source/weight hashes, element counts, nonfinite counts and bit/absolute errors against corresponding scalar HLSL stages before comparing against optimized wave kernels. Test shift padding/crop, C256 height4 wrap, and pool masked rectangles independently with exact finite lattice values. A compiled module alone is not a numerical or performance result.


## Dynamic differential host

`multihead_validate.cpp` loads the original scalar `native_c64.hlsl` with all wave/QKV/fast-FP8 macros disabled, using the same FFN→attention→projection sequence as scalar NativeC64. It binds the original weights and exposes FFN and AV readbacks without editing production headers. This isolates scalar HLSL math before optimized wave changes.

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static Development/HIP/multihead_validate.cpp -o multihead_validate.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

CLI: `multihead_validate.exe ASSETS MODULE OUTPUT_PREFIX [CHANNELS=64|512]`.

Default C64 uses real `block5-ffn.f32` (36,928 floats) and `block5-attention.f32` (24,642 floats), runs8×8 and16×16 with two deterministic patterns (FP8 lattice and non-lattice float values), and compares FFN, attention AV and raw projection outputs. It then reruns HIP attention on **the exact D3D FFN output** to isolate attention errors from FFN drift. Source assets need native_c64.hlsl and its original include files; no released DLL is changed.

Optional C512 loads `block23-attention.f32` (1,114,640 floats) and tests attention-only8×8 for both patterns, bypassing FFWD. This tests precisely the shared multihead attention formulas rather than pretending C512 uses the multihead FFN.

The host resets optimization flags, initializes outputs to NaN sentinels, synchronizes before comparisons, writes inputs and both backends' stage outputs, and reports bit/numeric/nonfinite/max-error counts. HIP QKV/norm/ex/prob intermediates are also saved. Exit0 requires exact bits, exit1 denotes API/nonfinite failure, exit3 denotes finite differences for investigation. GPU execution is scheduled by the parent process; cross-compilation does not claim numerical success. Parent must ensure HIP device0 and selected AMD D3D adapter are the same intended card.

For full hostgraph reuse, pool_project with C32 computes one32-product group followed by H() and F(), producing64 channels with unchanged matrix layout. C512 attention uses sixteen32-channel groups; C512 spatial operations are enabled separately. The host validates buffer sizes for doubled pool-projection channels.

Extended-guard module also compiled successfully via COMGR on2026-09-14:111,752 bytes, same isolated remote path and refreshed local release artifact. No GPU kernels were run during this update.

Hardware baseline update: C64 block5 at8×8/16×16 and C512 block23 attention at8×8 both passed all reported scalar-HIP/scalar-HLSL comparisons with bitdiff0 and invalid0 (`release/HIP/mh64-validation.log`, `mh512-validation.log`). WMMA migration is separately documented and tested; these reference results must not be attributed to the new WMMA module.

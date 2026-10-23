# Production-rounding dense fast candidate

This module is independent of exact `multihead_reference`, naive WMMA and tiled modules. It deliberately targets selected900p production arithmetic, so the legacy exact golden is not its acceptance oracle. See `PRODUCTION_ROUNDING_AUDIT.md` for runtime flags, final CSO writer and source-line evidence.

## Implemented contracts

All external inputs/weights/outputs stay float32 with original offsets. Block512, grid=ceil(M/64)×ceil(N/64), static LDS4KiB, M/N masking follow the tiled candidate. FP8 matrix operands must already be finite E4M3 lattice. Residual features/scales are not FP8-packed.

The accumulator persists **across both K16 instructions and all K32 chunks**. It is never reset/reduced through H between chunks. ISA_HALF defaults on in this module. Precise-chain polynomial disables contraction/reassociation.

| Entry | Arguments | Result |
|---|---|---|
| `mh_ffn_expand_fast` | input,weights,hidden,tokens,C | F(a×(g×(abs(g)×−.055908203125+.447265625)+.89453125)), g=clamp(a,−4,4); no intermediate H |
| `mh_ffn_contract_fast` | hidden,weights,middle,tokens,C | F(H(full FP32 dot)) |
| `mh_ffn_project_fast` | middle,feature,weights,output,tokens,C | Initialize H(feature×skip), MAC continuously, direct F; matches scalar-residual MAP_FEATURE+DIRECT_CAST variant |
| `mh_qkv_fast` | input,weights,qkv,tokens,C | Unrounded FP32 QKV[p][part][C]; must be followed by production fast normalization, not exact half-tree normalize |
| `mh_attention_project_fast_scalar` | av,feature,weights,output,tokens,C,post | Explicit scalar-residual diagnostic: initialize H(feature×skip); post0=F(H),3=H,4=F |

FFN entries support C64/128/256; QKV/attention diagnostic also C512. `mh_attention_project_fast_scalar` **does not implement NATIVE_MATRIX_RESIDUAL**, where production seeds through three FP8 diagonal matrices without initial H. It must not be wired to stream variants that require that contract. Fast QKV normalization, full attention, matrix-residual seeding and pool fast rounding are not yet implemented here.

The contract F(H) at the end of fused FFN is intentional: current bench.ps1 first builds HW_QUANTIZE=1 at line320, then overwrites the same CSO at329 without that macro. The final default0 retains contract-end H. Likewise PRECISE_CHAIN=1 at the final write means polynomial FMA contraction is not silently allowed.

## Real production HLSL validator

`multihead_fast_validate.cpp` does not reimplement an HLSL oracle. It loads the supplied **existing production fused-FFN CSO**, uploads row-major FP8 input and the same tile-packed FP8 weights used by NativeC64, runs the actual fused shader, and compares its FP8-decoded output to HIP fast expand→contract on the same float32 data. Hidden is saved on the HIP side for diagnosis.

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static Development/HIP/multihead_fast_validate.cpp -o multihead_fast_validate.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

```text
multihead_fast_validate.exe ASSETS PRODUCTION_FFN_CSO FAST_MODULE OUTPUT_PREFIX [64|128|256]
```

Use `native_wave_ffn_fused_fp8act_c64.cso`, `_c128.cso` or the unsuffixed C256 `native_wave_ffn_fused_fp8act.cso` from the current production asset set. The CSO must be the final `NATIVE_TILED_WEIGHTS=1` build; passing an unrelated or earlier untiled CSO invalidates the comparison. The EXE needs the existing Agility721 directory beside it, as with other D3D WMMA probes. The host enables experimental shader support, checks exact FP8 weight conversion, initializes outputs with sentinels, fences both APIs, and compares two deterministic patterns at M400. It saves input, production contract, HIP contract and HIP hidden floats. Exit0 means all compared bits match; exit1 denotes API/nonfinite failure; exit3 denotes finite differences.

This validates the **pair** expand→contract, not hidden values individually or the additional projection/QKV exports. It is the first production parity gate; it does not establish full900p fast-graph compatibility or performance.

## Build

COMGR3/Clang21 with ISA_HALF produced39,760 bytes at `D:\DLSSNR-Lab\hip-backend\multihead-fast.hsaco` and `.s`. MinGW host cross-compilation passed. No GPU execution was performed by the authoring agent, and no exact module, graph, public API or installed release was changed.

## Final-H RTZ investigation

Initial production FFN comparisons were finite but differed: C64 patterns132/160 values; C128294/160; C256266/160. They do not establish an accumulation/activation defect. Another production probe identified explicit HLSL `f32tof16` as RTZ on the current D3D path, distinct from Matrix.Cast<F16> RNE.

The independent fast module now retains original `mh_ffn_contract_fast` (RNE) and adds same-ABI `mh_ffn_contract_fast_pre` (unrounded FP32 accumulator) and `mh_ffn_contract_fast_rtz` (explicit `v_cvt_pkrtz_f16_f32` then F). The validator runs all three from exactly the same hidden buffer, saves pre/rtz arrays and prints RTZ_DIAGNOSTIC. Its original exit/report still reflects the RNE path, so exit3 can coexist with zero RTZ differences; inspect the labeled result.

Run `python3 Development/HIP/compare_fast_contract.py OUTPUT_PREFIX` on the downloaded files. It independently computes IEEE RNE and RTZ half conversion from pre-round floats, then E4M3 nearest-even quantization. Only if CPU-RNE agrees with HIP-RNE, CPU-RTZ with HIP-RTZ, and CPU-RTZ with production does it report that final RTZ alone explains the difference. This is a testable hypothesis until GPU diagnostics are run. Exact/reference modules were not changed. Updated module compiled to51,848 bytes.

## Confirmed production RTZ, now default

Root GPU tests found zero differences for the RTZ candidate in all C64/128/256 patterns. Read-only retrieval and `compare_fast_contract.py` independently confirmed all six cases: CPU RNE=HIP RNE, CPU RTZ=HIP RTZ, and CPU RTZ=production. Thus the original132/160,294/160,266/160 differences are fully explained by final-half RTZ on these fixtures. This does **not** mean Matrix.Cast<F16> is RTZ; the earlier matrix-cast probe agreed with RNE.

`mh_ffn_contract_fast` now uses the verified RTZ epilogue. The old RNE contract remains as `mh_ffn_contract_fast_rne`; pre and explicit rtz diagnostic aliases remain. The validator's main result/exit now tests default production RTZ, while RNE differences are labeled diagnostics. `compare_fast_contract.py` uses the explicit rne file when present and remains compatible with the earlier artifacts.

## Next independent family: raw QKV plus production fast normalization

`mh_qkv_normalize_fast(qkv,weights,normalized,tokens,channels)` uses block256 and grid ceil(tokens×heads/256). C64/128/256/512 are supported. Both qkv and normalized use **[pixel][part Q,K,V][channel]**, length tokens×3C floats. The input is raw FP32 output from `mh_qkv_fast`. Q/K squares and32-element sum remain FP32 with no intermediate H; inverse is native rsqrt(max(sum,epsilon))×scale for Q and rsqrt for K. The multiply and FP8 quantization are separate, and V is directly quantized. This implements production `NATIVE_QKV_FAST2=0`; it does not claim the alternative half-square-MMA variant.

New independent host:

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static Development/HIP/multihead_normalize_fast_validate.cpp -o multihead_normalize_fast_validate.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

```text
multihead_normalize_fast_validate.exe ASSETS PRODUCTION_QKV_NORMALIZE_CSO FAST_MODULE OUTPUT_PREFIX [64|128|256|512]
```

Use the real `native_wave_qkv_normalize_fp8qkv_c64.cso`, `_c128.cso`, unsuffixed C256, or `_c512.cso` with **NATIVE_TILED_WEIGHTS=1, NATIVE_INPUT_TILED=0, NATIVE_QKV_FAST2=0**. Do not supply the C512 stream/tiled-input variant: the host deliberately uploads ordinary row-major input. It reads original block5/9/15/23 attention weights, packs the matrix tiles exactly, binds the original full attention buffer for scales, runs actual production QKV+normalize and compares to HIP raw-QKV→fast-normalize. Production window-major output bytes are independently converted back to raster[p][part][C]. It tests two patterns at16×16, saves input/raw HIP QKV/production normalized/HIP normalized, and reports exact bits/nonfinite/max error. The host enables Agility721 experimental shader support and needs the D3D12 SDK folder beside the EXE.

The normalization family has only compiled so far; GPU parity is pending. Projection variants still require their own production checks, particularly scalar-residual RTZ versus three-diagonal matrix residual, so they are not promoted by the FFN result. Probability/attention-projection families remain subsequent work.

## QKV normalization passed; attention/projection candidates

Root production-CSO tests now report zero bit differences and zero invalid values for QKV→fast-normalization at C64/128/256/512, both patterns (`release/HIP/mh*-norm-fast-validation.log`). That family is validated on those fixtures.

New same-layout stages:

| Entry | Exact arguments | Launch |
|---|---|---|
| mh_scores_exp_fast | normalized,weights,ex,width,height,C | block32; grid windows×heads×16 |
| mh_probabilities_fast | ex,prob,windows,C | block32; grid windows×heads×4 |
| mh_attention_av_fast | prob,normalized,av,width,height,C | block32; grid windows×heads×8 |
| mh_attention_project_fast_matrix | av,feature,weights,output,tokens,C,post | block512; grid ceil(tokens/64)×ceil(C/64) |

Normalized input is raster[p][Q,K,V][C]. ex/prob are `[window][head][query64][key64]`; AV/projection output raster HWC. C64/128/256/512 are accepted, width/height must be divisible by8. Scores use FP8 WMMA; affine half-bit exponent uses explicit RTZ with no earlier score H. Probability denominators reproduce production's two32-key partials through F16 WMMA against ones: side0 gathers keys0..15 and32..47, side1 gathers16..31 and48..63. It forms unrounded inverse and directFP8 probability. AV carries FP32 across all64 keys and quantizes directly, without an intervening or final H.

Matrix-residual projection decomposes each original scale into three FP8 components exactly as NativeC64's host packing, including the special subnormal round/clamp-to-seven rule. Each component is a diagonal K32 matrix; three two-K16 WMMA operations seed the accumulator before the main matrix. Feature must be exactFP8. No initial H is inserted. Scalar/mapfeature projection now explicitly uses initial **Hrtz**, matching the production explicit-half conversion result. Both projection forms use post0=F(Hrtz), post3=Hrtz, post4=directF. Original exact modules are unchanged.

### Real production attention and projection host

```text
multihead_attention_fast_validate.exe ASSETS FAST_MODULE ATTN_CSO SCALAR_PROJ_CSO MATRIX_PROJ_CSO PREFIX C PATTERNS
```

`PATTERNS` is1 or2. Host source is `multihead_attention_fast_validate.cpp`; cross-build with the same MinGW/D3D libraries as the other production validators. Use:

- Attention: `native_wave_attention_direct_fp8qkv_fp8act[_c64|_c128|_c512].cso` (C256 unsuffixed), ATTN_FAST2=1.
- Scalar/mapfeature direct-FP8 projection: `native_wave_project_mapfeature_fp8act_f8out[_c64|_c128].cso` (C256 unsuffixed).
- Matrix-residual direct-FP8 projection: `native_wave_project_mapoutput_fp8act_f8in_f8out[_c64|_c128].cso` (C256 unsuffixed).
- Either projection path may be `-` to skip it; e.g.C512 attention-only until its matching direct-output variant is selected. Do not pass a float32-output CSO to this byte-output host.

The host generates two bounded FP8 normalized-QKV patterns, independently maps HWC to production window-major bytes, invokes the actual attention CSO, and compares HIP scores→probabilities→AV. It saves HIP ex/prob for localization. Projection tests deliberately consume the exact **production AV** on both backends so attention drift cannot contaminate their result. It packs the original attention projection matrix/scales/three diagonal matrices, tests scalar residual as float32 (second pattern off-FP8 grid), matrix residual as FP8, and compares direct-FP8 outputs. All outputs are sentinel-initialized and fenced.

These new attention/projection branches have compiled but have not yet been GPU-validated. RAW/post3 and post0 outputs, nonzero map padding, and other projection CSO storage variants are not covered by this initial host; do not infer their parity from a direct-output-only result. Updated fast module:138,712 bytes. Root schedules GPU execution; this authoring agent did not run it.

## RAW / C512 storage variants and production pool projection

Root has validated the preceding attention path at C64/128/256/512 and direct-output scalar/matrix projection at C64/128/256, both patterns, with zero differences (`release/HIP/mh*-attn-fast-validation.log`). Remaining formats are tested independently below.

The attention/projection host now accepts optional arguments after PATTERNS:

```text
[POST=4|3|0] [SCALAR_FEATURE=0:f32|1:fp8row|2:fp8tiles] [INPUT_TILED=0|1] [OUT_FP8=0|1]
```

POST selects HIP mathematics:4=directF,3=Hrtz raw,0=F(Hrtz). OUT_FP8 independently selects production storage; defaults to1 for POST4 and0 otherwise. This separation matters: C512 stream18 does F(Hrtz) but stores FP8 bytes. Projection byte/float32 allocations, readback lengths and decoding follow OUT_FP8; the initial attention comparison always remains FP8 output. SCALAR_FEATURE applies to the scalar slot only; the matrix slot expects ordinary FP8 raster feature bytes. INPUT_TILED packs candidate production input in16-token×32-channel byte tiles; HIP always receives its original float32 HWC ABI. Current fixture map padding stays0.

Examples of actual C512 production variants (use scalar slot, matrix slot `-`):

- `native_wave_project_stream1raw_c512.cso`: POST3, SCALAR_FEATURE2, INPUT_TILED0, OUT_FP80.
- `native_wave_project_stream18_c512.cso`: POST0, SCALAR_FEATURE2, INPUT_TILED0, OUT_FP81.
- stream0 variants need INPUT_TILED1 and the appropriate scalar feature representation.

Bench.ps1:674 does not enable MATRIX_RESIDUAL for C512 stream1. Do not test that actual runtime variant through the three-diagonal HIP entry simply because its feature happens to be FP8. C64/128/256 raw matrix-residual variants use `native_wave_project_raw_mapoutput_fp8act_f8in[_cC].cso` with POST3/OUT_FP80 in the matrix slot.

### Pool projection audit and entry

Production `native_wave_head_project.hlsl:17-22` (C64/128/256/512) still uses F16-input WMMA, separate zero-seeded K32 sums, software-H RNE after each addition, then F. Bench.ps1:603/610 defines only MATRIX_CHANNELS: there is no fast-accumulation branch to exploit here. `native_wave_c32_ds.hlsl:10/32` instead uses FP8 operands for its single K32 dot and explicit-half RTZ before F. Pooling itself retains its original half tree; it is not changed in this update.

New export `mh_pool_project_production(pooled,weights,output,width,height,valid_width,valid_height,C)` retains the external float32 ABI. Launch block32 and grid ceil(width×height/16)×(2C/16). C32 uses native FP8 WMMA plus final Hrtz; other supported C values use native F16 WMMA plus per-group H_RNE. Neither is a fallback disguised as another instruction. The F16 path requires exact finite half weights/activations; the C32 path requires exact finite FP8.

```text
multihead_pool_production_validate.exe ASSETS FAST_MODULE POOL_PROJECT_CSO PREFIX C
```

This new host uses actual `native_wave_c32_ds.cso` for C32, `native_wave_head_project_c64/c128/c256.cso` or unsuffixed C512 `native_wave_head_project.cso`. It loads real block4/8/14/22 DS or head-matrix weights, checks and packs the appropriate operand format, supplies16×16 pooled FP8 fixtures in two patterns, reads the production float32 output and compares with HIP. It validates projection separately; no new pooling formula or mask behavior is inferred from it. Correct work_width/crop constants are supplied for C32.

New host/module builds passed. Fast module now149,320 bytes. The root will run RAW/C512/pool GPU tests; no further remote module overwrites should occur during that validation. Subsequent LDS-stride padding is a separate candidate, not part of these numerical changes.

2026-09-15: all documented production FFN/QKV/attention/projection/RAW/C512/pool fixtures passed; logs under release/HIP. Whole-network matching remains outstanding.

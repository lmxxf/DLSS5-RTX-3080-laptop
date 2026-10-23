# 900p production deep/ViT precision audit

Scope: the configuration in `Development/900p/game-flags.txt`; production binaries still need per-stage differential validation. This is **not** a claim that the old HLSL is wrong. The precise reference reproduces the original scalar network, while the shipping optimized network deliberately uses different rounding schedules.

## ViT matrices (new module ready for validation)

`deep_fast.hip` exports `vit_expand`, `vit_project`, `vit_qkv_project`, `vit_qkv_normalize`. Parameters/layout match the reference, with one **launch difference**: fast normalize dispatch work_items=`tokens*3072` (16 token×16 channel output tiles), not reference `tokens*96` (one thread per head). All use flat grid ceil(work_items/256), block32. Tokens divisible16; weights remain original f32 arrays. MLP matrix operands must be exact finite E4M3; QKV weights/input are finite half. QKV output is raw F32, intermediate normalized output F8-valued f32.

- **Expand1024→4096**: `native_wave_vit_blocked.hlsl::expand`, especially BLOCK_M>1 body, accumulates all1024 channels in F32 using FP8 MMA; `Activate` evaluates the polynomial without H(dot) or nested half rounds, then applies F. Reference H-rounds every32 channels and the polynomial. Hidden packing is independent: production has tiled E4M3 bytes, HIP exposes raster f32 values on that same lattice.
- **Contract4096→1024**: `NativeVitLinear::SplitK` selects split-K only for4096 when `DLSS5_VIT_SPLIT_K=1`. `native_wave_vit_blocked.hlsl::reduce` computes four independent F32 partials. `combine` starts with **handwritten-RNE H(residual*scale)**, adds all four partials in F32, then F(H(sum)). Reference seeds the residual into partition0 and H-rounds every K32 and partition merge. New HIP preserves production's residual placement.
- **Attention projection1024→1024**: split-K1 does not select this shape. `native_wave_vit_blocked.hlsl::reduce` non-split branch retains four partitions, with H(residual*scale) seeded into partition0, F32 accumulation within each, F32 partition addition, final F(H(total)). Handwritten H is RNE here, **not** driver explicit-conversion RTZ.
- **QKV+norm**: `native_wave_vit_qkv.hlsl::project_fused` accumulates all1024 channels with F16 MMA, no original512 split/H. Q/K each square rounds through `Matrix.Cast<F16>` (RNE proven for the analogous production C32 norm), followed by F32 MMA sum against ones. Scale is F32 `rsqrt(max(sum,epsilon)) * (5.65625*head_scale)` for Q, rsqrt for K; final F8 cast. Reference uses H output, tensor permutation, half-square pair correction/tree, H inverse, and H multiplications. Both have the same tensor dimensions; this is a precision difference, not a reason to pad240/400 to virtual tokens.

**Do not blanket-change H to RTZ.** ViT blocked linear helpers are integer RNE; FAST4 explicit f32tof16 was RTZ; matrix casts remain RNE. The conversion site determines semantics.

Validation host: `deep_fast_validate.exe ASSETS FLAGS DEEP_FAST_HSACO OUTPUT_PREFIX`. Real block31 weights, NativeVitLinear/NativeVitQkv with supplied production flags,64 tokens and two patterns. Isolates contract by uploading the same HLSL hidden values to HIP. Saves both sides for expand/contract/normalized-QKV/projection. New executable requires Agility721 beside it for the HLSL oracle. No existing HIP graph/API modified.

## ViT attention (remaining production mismatch)

`native_wave_vit_attention_fp8.hlsl`: QK raw F32 dot; affine→explicit `f32tof16` before the original exponent bit map; denominator F32 MMA over real keys only; inverse F32; AV F32 MMA across keys; output `F(H(acc*inverse))` with H defined as explicit f32tof16. Based on independently validated C32 conversion behavior, **affine and final AV H are RTZ candidates that require direct ViT production verification**. Current `deep_reference.hip::*_fast` uses RNE at these two sites. No dummy attention tokens may be inserted. Matrix sum order and tail mask must match240/400.

## Split C512 (not yet implemented in deep_fast)

`NativeSplit` selects stream8 variants (`native_wave_split_ffwd_parallel_streamf/stream8.cso`) despite `DLSS5_TEST_WAVE_SPLIT_FFWD=0`: stream choice precedes that flag. `native_wave_split_ffwd_parallel.hlsl` WAVES4 path:

-512 mix: entire K512 F32 MMA accumulation, then F(H(total)).
-8 grouped64→256 expands: entire K64 F32 MMA, then Activate(H(total)).
-256→64 contract per group: entire K256 F32 MMA, then F(H(total)).
-`NATIVE_HW_H` determines whether those H sites use explicit half conversion; inspect actual built macro/ISA before substituting RTZ. Stream production build inherits `DLSS5_BUILD_HW_H` through `scripts/bench.ps1`.
-FFWD/attention residual projections use `native_wave_project.hlsl`, streamed FP8 operands and feature layouts. Initial residual and accumulator placement differ from the scalar H-per-K32 reference; source and built flags need dedicated isolation before implementing. Attention-project stream1 build explicitly enables HW_H=1; stream0 uses its own build path and must not be assumed identical.

## Decoder upsample (remaining)

`native_wave_decoder_linear.hlsl` FAST_ACCUMULATE path retains4 partitions for1024 inputs (one otherwise), but accumulates each in F32 and merges in F32, then H(total) once. Epilogue adds F(skip)*scale and H again; C32 retains raw H, others F. `NATIVE_DECODER_HW_H` controls explicit conversion. Existing reference does H after every K32 and every partition. OUT16 storage writes already-H/F values, so that final packing itself is exact; the significant differences occur before it. Crop/nearest2× geometry remains unchanged.

## Validation and implementation update (2026-09-15)

`release/HIP/deep-fast-all-validation.log`: ViT matrix/norm/attention, decoder1024/512/256/128/64, and split FFWD all passed two-pattern GPU comparisons bitdiff0. ViT expand's six signed-zero differences were traced to its **outer activation FMA**, not a rule to retain every exact −0. The module keeps F(exact±0)=+0 and explicitly fuses the outer polynomial multiply-add, matching the production tiny negative values that subsequently quantize to −0.

New `deep_fast.hip` now also exports the three production ViT attention kernels, decoder_project2x and split mix/expand/contract/projection. Special inverse launch: work_items=`T*32*16`; score=`T*T*32`, AV=`T*1024`. Attention affine and final AV explicit half conversions use validated RTZ; matrix half casts remain RNE. Decoder H remains the production integer-RNE helper. Split FFWD uses production full-K F16 accumulation and final RTZ at its explicit H sites.

The stream0 split projection validation uses the **existing shipped** `native_wave_project_stream0f_c512.cso`, with actual tiled FP8 input/weights/output and raster f32 residual. `deep_fast_validate.exe ... OUTPUT_PREFIX 400` now covers the real400-token ViT and this projection;64 additionally accepts an optional split FFWD oracle CSO path. Stream0 projection result is pending this final check. No graph dispatch is changed by these tests.

2026-09-15: ViT64/400 and attention, decoder five shapes, split FFWD and stream0f projection passed both production fixtures. The six signed-zero expand differences required outer polynomial FMA; F(0) remains canonical +0.

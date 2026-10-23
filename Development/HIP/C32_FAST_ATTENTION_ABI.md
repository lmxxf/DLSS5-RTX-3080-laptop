# C32 production FAST4 attention

Independent module `c32_fast_attention.hip`, preserving the exact reference module. Input is **already-computed raw half-valued FFN output**, tile-major `[window][64][32]`, stored as f32. This module does not compute FFN or Gaussian prefix.

All kernels launch `grid.x=ceil(work_items/256)`, block `(32,1,1)`, shared0. Tokens `T` must be divisible64; windows `N=T/64`. Device weights are original8225 f32 values (`block*-attention.f32`), not packed host weights. Matrix coefficients must be exactly finite E4M3 representable. No scalar matrix fallback.

| Symbol | Parameters | Work items |
|---|---|---:|
| c32_fast_qkv | raw_input, weights, qkv, T | 96T |
| c32_fast_normalize | qkv, weights, normalized, T | 96T |
| c32_fast_scores | normalized, weights, ex, N | 4096N |
| c32_fast_probabilities | ex, prob, N | 4096N |
| c32_fast_av | prob, normalized, av, N | 32T |
| c32_fast_project | av, raw_input, weights, output, T, raw_output | 32T |

Scalar dimensions unsigned32; pointers f32 GPU storage. QKV/normalized `[part3][T][32]`; ex/prob `[window][query64][key64]`; AV/output `[T][32]`. No aliasing. All outputs fully written under valid geometry. FP8 conversions saturate finite overflow as production SAT_CAST. Raw projection result remains H when raw_output1, otherwise additionally F.

**All six attention stages must switch together**:

- QKV uses F(input) × FP8 weights, retaining raw F32 dot (exact reference rounds H).
- Q/K norms sum H(each square) via F16 WMMA to F32; no original half-square correction/tree or H(rsqrt). Q scales by original f32 weight8192 before final F. V is F(raw dot).
- Scores add original bias in F32; affine approximation uses F32 input arithmetic followed by explicit half RTZ and the original half-bit exponent map. No H(score+bias), no ordinary exponential.
- Probability denominator sums exponent half values with native F16 WMMA, F32 accumulation across64 keys. Output F(ex*(1/sum)), no H inverse or intermediate H product.
- AV uses native FP8 WMMA F32 accumulation across64 keys followed by F; no H per32-key group.
- Projection adds raw_input*residual_scale without pre-rounding that product, then explicit half RTZ(sum). Multiplication/addition are kept separate, matching production PRECISE_CHAIN/fused-FFN behavior.

Normalization/probability currently recompute row reductions per16-channel output tile. This preserves the simple flat launch contract while using matrix cores; fusion can remove duplication after validation.

`c32_fast_attention_validate.exe ASSETS HIP_MODULE ORACLE_CSO OUTPUT_PREFIX`: two16x16 half-valued input patterns, real block1 attention weights. Compares final raw output against original `native_wave_c32_split_attention.hlsl` FAST4 code with fusedFFN/epilogue disabled solely to expose a standalone attention boundary. Saves all HIP stages and D3D final. `compile-c32-fast-oracle.ps1` builds that oracle, no GPU launch. Driver requirements apply only to D3D validation EXE (Agility721 beside it), not HIP module.

Compile-only result: COMGR3/Clang21 gfx1201,43904 bytes. GPU testing before production HW_H switch: both patterns, all six stages bitdiff0 after explicit exp conversion was corrected to RTZ. Production HW_H=1 projection RTZ is now under test. Existing exact reference remains separately available; production math differences are intentional but correctness against production must be measured.

Production HW_H=1 final validation also passed: both patterns and all six intermediate stages bitdiff0/nonfinite0 (`release/HIP/c32-fast-attention-hwh.log`). Norm Cast<F16> stays RNE; explicit exponent and final projection conversions use RTZ.

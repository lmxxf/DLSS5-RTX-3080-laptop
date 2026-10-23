# Multihead WMMA backend: first operator implementation

`multihead_wmma.hip` replaces the selected GEMMs with native gfx1201 FP8 WMMA. It is not yet a fused/optimized whole backend. All external buffers and original weight offsets remain float32, and every entry preserves its scalar reference argument order with a `_wmma` suffix. Normalization, probabilities, shift/crop and pooling stay in `multihead_reference.hip`.

The scalar baseline is now hardware-validated: `release/HIP/mh64-validation.log` and `mh512-validation.log` both end with zero bit differences and zero invalid values. These are baseline results, not validation of the new WMMA operators.

## Dispatch and numerical contract

All WMMA entries use **one-dimensional32-thread blocks**, wave32. Dense stages use grid `ceil(M/16)*(N/16)`; one block computes16 rows×16 columns. Every N is a16 multiple. When M is a16 multiple—as in current whole-network shapes—this equals `work_items/256`, where work_items=M×N. `ceil(M*N/256)` is **not** the general tail-M formula; use the tile formula. Dense kernels zero-fill rows past M and omit their stores.

| Export | M | N | K | Channels |
|---|---:|---:|---:|---|
| mh_ffn_expand_wmma | tokens | 4C | C |64/128/256|
| mh_ffn_contract_wmma | tokens | C | 4C |64/128/256|
| mh_ffn_project_wmma | tokens | C | C |64/128/256|
| mh_qkv_wmma | tokens | 3C | C |64/128/256/512|
| mh_attention_project_wmma | tokens | C | C |64/128/256/512|
| mh_split_project_wmma | tokens | C | C |64/128/256/512|
| mh_pool_project_wmma | width×height | 2C | C |32/64/128/256/512|

Argument signatures are exactly those of the corresponding entries in `MULTIHEAD_REFERENCE_ABI.md`. QKV output is `[pixel][part][channel]`, so treating the three parts as one3C-wide matrix preserves the existing layout. Pool width/height are pooled output dimensions; its optional valid rectangle is preserved.

For score/AV matrices, the flat block ID maps first to window/head, then to a tile:

- `mh_scores_exp_wmma`:16 blocks per window/head (4query tiles×4key tiles), each GEMM16×32 times32×16; grid=windows×heads×16. Output remains `[window][head][query64][key64]` after the original bias/H/half-bit exponential.
- `mh_attention_av_wmma`:8 blocks per window/head (4query tiles×2channel tiles), grid=windows×heads×8. Two32-key groups, each with its own H() boundary; output is mapped back to raster HWC. V is F(H)-quantized exactly where the scalar reference consumes it.

Each32-product group is computed by **two K16 FP8 WMMA instructions with accumulator initially zero**. The resulting group sum is then added to the running value and rounded through H(). Residual multiplication/H() initializes the running value before the first group, but **does not seed the WMMA instruction**. This distinction preserves the scalar `H(previous + sum(K32))` structure and avoids the known C-placement difference. FFN gate constants, F()/H() boundaries, attention bias/exponent mapping and raw-output option are unchanged.

Matrix operands must already lie on the **finite E4M3 lattice**. The FP8 conversion packs those values; it does not add an F() quantization step to the reference math. In particular first-stage GEMM input must not be arbitrary H/raw float values. Residual `feature` values and scalar scales are not FP8-packed and may be ordinary finite float32/half values. Matrix weights must be checked independently of bias/scale/residual values. Unsupported compilers fail on the intrinsic requirement; there is no scalar or F16 fallback disguised as FP8.

## Build state

COMGR3/Clang21 SDKless compilation succeeded, producing182,096 bytes at `D:\DLSSNR-Lab\hip-backend\multihead-wmma.hsaco` plus `.s`. Refreshed local copies are in gitignored `release/HIP/`. No HIP header, device library, graph/API changes or GPU execution were performed by this agent. The code object's native instructions should be inspected and the host below run before enabling graph dispatches.

## Per-stage validation host

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static Development/HIP/multihead_wmma_validate.cpp -o multihead_wmma_validate.exe
```

```text
multihead_wmma_validate.exe ASSETS SCALAR_MODULE WMMA_MODULE OUTPUT_PREFIX [C=64|128|256|512|32]
```

It tests two distinct finite FP8 lattice patterns on16×16 (C512:8×8). Real weights are block5/9/15 for C64/128/256 FFN+attention and block23 for C512 attention. Pool weights are block4/8/14/22-ds for C32/64/128/256 and head-matrix for C512. C32 tests pool projection alone. All matrix weight ranges are explicitly checked against the254 finite E4M3 encodings, excluding scales/biases from that requirement.

Every WMMA stage consumes exactly the same scalar intermediate as its reference; differences are isolated instead of cascading from a previous candidate. Tests include expand, contract, FFN project, QKV, score-exponent, AV, attention project and pool project. Normalized QK, probabilities, pooled/hidden/middle/FFN operands are read back and checked for lattice membership before their FP8 GEMM. Outputs use NaN sentinels, explicit synchronization and bit/nonfinite/max-error reports. All scalar/candidate stage arrays are saved. Exit0=all bit-exact; exit1=API/contract/nonfinite failure; exit3=finite numerical differences requiring investigation.

This host does not yet exercise `mh_split_project_wmma`, masked pool rectangles, tail-M matrices or complete chains of WMMA candidate outputs. Those require follow-up validation before those usage modes are enabled. The observed FP8-versus-HLSL WMMA agreement does not remove the need to check each migrated epilogue and reduction boundary.

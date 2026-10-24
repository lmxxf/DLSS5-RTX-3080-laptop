# Shared-operand64×64 multihead dense candidate

This independent module does not replace `multihead_wmma.hip`, modify the graph/API, or deploy an installed DLL. It is a first dense-family reuse experiment. Numeric and performance GPU results are pending.

## Launch and storage

Every family entry keeps the corresponding scalar argument order and uses a `_tiled` suffix:

| Entry | M | N | K |
|---|---:|---:|---:|
| mh_ffn_expand_tiled | tokens |4C|C|
| mh_ffn_contract_tiled | tokens |C|4C|
| mh_ffn_project_tiled | tokens |C|C|
| mh_qkv_tiled | tokens |3C|C|
| mh_attention_project_tiled | tokens |C|C|
| mh_pool_project_tiled | width×height |2C|C|

Channels and original float32 tensor/weight layouts follow `MULTIHEAD_WMMA_ABI.md`. Normalization, scores/AV, probabilities and spatial/pool arithmetic are not part of this candidate. Pool projection includes its original valid-rectangle mask.

Launch **grid `(ceil(M/64)*ceil(N/64),1,1)`, block `(512,1,1)`, dynamic shared bytes0**. Sixteen wave32 groups form a4×4 arrangement of16×16 WMMA output tiles. M and N tails are both masked on input loads and output stores; all512 threads still participate in both barriers. Invalid rows/columns are zero-filled. M400 and N32 are deliberate test cases, not assumed divisible by64.

Static shared storage is4,096 bytes: packed A[64][32] and transposed-stored B[N][K] tile[64][32], two8-bit arrays expressed as512uint32 words each. Each thread loads four A floats and four B floats, uses two pair-conversion instructions per operand to create one4-byte FP8 word, then writes one word to each shared array. Four output waves reuse each operand row. After the first barrier, every wave reads two packed words per K16 fragment; the second barrier prevents overwrite until all fragments have been loaded. No async copies or double buffering are introduced yet.

Each K32 group's two WMMA instructions start at zero, then the group sum is added to the running result and H()-rounded. Skip/residual multiplication remains outside FP8 conversion and outside the WMMA seed. Original gate/F()/H(), RAW_OUTPUT and QKV[p][part][C] behavior are retained. Matrix operands must already be finite exact E4M3; residual features/scales remain float32. No extra F() is applied to arbitrary input, and no fallback is hidden behind the entry name.

## Build inspection

COMGR3/Clang21 compiled the SDKless module to117,040 bytes at `D:\DLSSNR-Lab\hip-backend\multihead-tiled.hsaco`, with assembly in `.s`; local artifacts are in gitignored `release/HIP/`. Metadata reports4KiB static LDS, zero private segment/scratch, and wave32 for all seven entries. Expand/contract/QKV/pool use35 VGPRs; residual projections use74; the generic probe uses73. This is compiler metadata, not a measured occupancy or speedup. Assembly includes native FP8 WMMA and barriers around shared operand staging.

## Isolated validator

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static Development/HIP/multihead_tiled_validate.cpp -o multihead_tiled_validate.exe
```

```text
multihead_tiled_validate.exe ASSETS SCALAR_MODULE TILED_MODULE OUTPUT_PREFIX [C=64|128|256|512|32] [OPTIONAL_NAIVE_WMMA_MODULE]
```

The host is a separate file and leaves existing validators unchanged. It compares each candidate operator with the proven scalar stage on the same inputs, using original block5/9/15 or block23 weights and pool weights block4/8/14/22/head-matrix. Matrix weights and all consumed matrix activations must pass exact E4M3-lattice checks. Two distinct lattice patterns use M400; pool output M100 adds a different row tail. Attention projection receives a controlled lattice AV input, so no unimplemented score/AV candidate is implicitly tested.

An extra test-only `mh_dense_tiled_probe` accepts `(input,feature,weights,output,M,N,K,skip_offset,raw)` with matrix offset0 and K a32 multiple; skip_offset=~0u disables residual. The host runs M400×N32×K64 with exact small-integer inputs and compares against CPU sums. A256-float trailing canary must remain unchanged. This checks a half-empty N tile and masked final M tile, including no out-of-bounds stores.

If the optional naive module is supplied, each stage also records GPU-event timings for the corresponding previously implemented `_wmma` entry versus `_tiled`: three warmups then ten launches, unchanged input, same output buffer, no transfers inside the event interval. The naive launch uses its16×16 tile grid, the candidate its64×64 grid. These are isolated operator timings, not whole-network/frame FPS, and stage order/cache/clock effects remain. The optional path dynamically resolves event functions locally without modifying `hip_api.h`.

Outputs use NaN sentinels and explicit completion checks; reports include bit/nonfinite/max-error counts and raw stage arrays. Exit0 requires exact comparisons, exit1 denotes API/contract/nonfinite failure, exit3 finite differences. Optional timing does not excuse correctness failures. No GPU tests were run by the authoring agent.

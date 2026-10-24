# Fused production multihead attention

`multihead_fused_attention.hip` exports:

```cpp
mh_attention_fused(const float* normalized, const float* weights,
                   float* av, uint32_t width, uint32_t height,
                   uint32_t channels)
```

Launch `grid=(width/8)*(height/8)*(channels/32)`, block128, shared0. Each workgroup handles one8×8 window and one32-channel head using four wave32s. Width/height must be positive multiples8; C is64/128/256/512. Input/output disjoint. Input is normalized f32 raster `[pixel][Q,K,V][C]`, already on the exact finite E4M3 grid. Weights are the original f32 attention blob; output is raster `[pixel][C]`, exactly the AV boundary expected by the separate production projection.

No QKV generation, normalization, residual projection, pooling, or Gaussian work occurs here. The module fuses only the existing production `mh_scores_exp_fast → mh_probabilities_fast → mh_attention_av_fast`.

LDS: packed Q/K/V3×64×36 bytes=6912; ex64×66 half elements=8448. Once scores finish, probability64×68 bytes reuses dead Q/K space (4352 bytes within4608), leaving V untouched. Output AV goes straight to global f32. Three workgroup barriers delimit packed loads, score stores, probability stores. All four waves participate.

Math: FP8 WMMA scores, original per-head bias, explicitly RTZ affine half conversion then original exponent bit map. Denominator preserves MH's two32-key partial groups: keys0..15+32..47, separately16..31+48..63, F16 WMMA/F32 sums, then adds those partials. This intentionally differs from C32 FAST4's sequential64-key accumulator. Probability uses unrounded reciprocal and E4M3 quantization; AV accumulates all64 keys in F32 FP8 WMMA and writes direct F, without an H epilogue.

Compile-only COMGR3/Clang21 gfx1201 result:18416-byte hsaco; metadata LDS15360, VGPR103, SGPR18, private scratch0. No GPU correctness or speed claim follows from this metadata.

Validation executable:

```text
multihead_fused_attention_validate.exe ASSETS STAGED_MODULE FUSED_MODULE PRODUCTION_ATTN_CSO OUTPUT_PREFIX C [WIDTH HEIGHT]
```

Defaults16×16; accepts8-aligned sizes up to128×128 and all four C values. Uses two deterministic normalized E4M3 patterns and real per-family attention weights. Compares production-vs-staged, staged-vs-fused, production-vs-fused, saving all output arrays and inputs. Output sentinels, finite counts and bit/numeric/maxabs differences are checked. The D3D oracle alone requires Agility721. The graph is not modified.

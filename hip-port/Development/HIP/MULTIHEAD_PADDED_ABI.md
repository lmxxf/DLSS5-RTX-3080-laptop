# Independent stride9 LDS candidate

`multihead_fast_padded.hip` is a copy of the current validated `multihead_fast.hip` with only seven literal layout/index replacements in `fast_dense`: the two LDS arrays grow from512 to576 words, their producer writes use `row*9+word`, and the four fragment read indices use stride9 instead of8. Thread mapping, barriers, matrix order, half conversions, quantization, residual handling, public symbols and all non-dense kernels are unchanged.

Each logical operand remains64 rows×32 FP8 elements, stored as eight data words plus one unread padding word per row. The512 producers still write exactly eight words per row. CPU enumeration checked that every consumer word is written and no consumer accesses the padding word. This changes shared-memory address distribution; actual speedup must be measured rather than inferred from a bank-index formula.

## Artifacts

- Source: `Development/HIP/multihead_fast_padded.hip`
- New remote code object: `D:\DLSSNR-Lab\hip-backend\multihead-fast-padded.hsaco`
- New assembly: same path plus `.s`
- Read-only retrieved artifacts: `release/HIP/multihead-fast-padded.hsaco[.s]` (gitignored)
- Existing `multihead-fast.hsaco` was not overwritten.

Compiled with the existing SDKless COMGR3/Clang21 path for gfx1201. Code object149,320 bytes. Candidate SHA256:

```text
49799033101a3c19bd2a012016e4ca4c786d1187a34665438ca80598a93d5c9d
```

Source baseline SHA256 `5556b812d4d1956d8369154a771f233c554a49b53cea608fd877dd8bee7e720c`; padded source `1ca196a493faacc368a74d2b037fc42aead01acd7046765ff5f899085aa32125`. Baseline local code-object SHA256 `462bc389c0240f16c751af7c5580291b27b3e00bf71ca641147fa39a7f9c3764`.

## Metadata comparison

All14 kernel exports remain present with identical argument ABI. The nine entries that inline fast_dense change static LDS4096→4608 bytes. Their wavefront32, block512, zero private/scratch storage and SGPR counts remain unchanged. The other five stages retain their metadata.

| Dense entry | Baseline VGPR | Padded VGPR |
|---|---:|---:|
| ffn_expand_fast |32|32|
| ffn_contract_fast |30|30|
| ffn_project_fast |38|38|
| qkv_fast |32|32|
| attention_project_fast_scalar |38|38|
| contract pre/rtz/rne diagnostics |30|30|
| attention_project_fast_matrix |95|96|

There are no named undefined ELF symbols. The one-register increase in matrix projection is a material observation for whole-graph profiling; do not assume padding is universally beneficial.

## Acceptance

Pass this module filename to existing per-stage production validators without changing entry names or launch geometry. Then compare the complete graph against the current baseline on the same inputs and flags, including large900p shapes, before deciding whether to adopt it. Small M400 operator timings alone are insufficient. This authoring agent compiled and inspected the candidate but ran no GPU kernels and changed no installed release.

Later source extension: `multihead_fast_padded.hip` now also appends the independent wave-normalization entry described in `MULTIHEAD_NORMALIZE_WAVE_ABI.md`. The stride9-only hashes/metadata above record the earlier snapshot and binary, which was not overwritten. The appended source builds to the separately named `multihead-fast-padded-wave.hsaco`.

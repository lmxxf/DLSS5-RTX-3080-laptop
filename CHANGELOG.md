# Changelog

[中文说明](CHANGELOG.zh-CN.md) · [Back to README](README.md)

This file documents the detailed changes, benchmark numbers, configuration options, and SHA256 checksums for each release.

---

## 0.3.0 (2026-10-29)

Download: [Quark](https://pan.quark.cn/s/1ace87045701) · [Gofile Mirror](https://gofile.io/d/oR1ZAEvO)

All three packages use **PTX V3.1_pack5** (31-block Small / Preset 2 / Style 1, 15/15 O4 in original slots, `266,414,592` B):
- **Core Pipeline Upgrades (`V2.2 → V3.1_pack5`)**:
  - `V2.2`: Native `cp.async.mbarrier.arrive` completion binding + branchless SWAR `f16x2 → e4m3x2` quantization;
  - `V2.3`: 8-instruction `PRMT` (`0x9180 / 0xb3a2`) unpack;
  - `V2.4`: Just-in-time demand decoding + dead temporary register pool recycling;
  - `V2.6`: Low/High K16 layout + zero-copy `mapped` FP16 operand forwarding (removing 21,712 generated `mapped PRMT` sites);
  - `V2.7`: Selective `maxnreg 168` on four C32 kernels (increasing CUDA Occupancy API residency from 8 to 12 warps/SM);
  - `V2.9_fast → V3.1_pack5`: Unified normal/subnormal alignment via `mul.rn.f16x2 0x1c001c00` ($\times 2^{-8}$), hardware `HMNMX2 |R2|` absolute-value modifier folding, and single-instruction `LEA 0x007f007f` symmetric ties-toward-zero rounding, shrinking pair pack core SASS from **13 → 9 → 5 instructions** and reducing non-NOP static SASS across the 38 active FP8 kernels to **`152,076` instructions** (down from `175,685` in `V2.7` and `163,944` in `V2.9_fast`).
- **RTX 3080 Laptop Model GPU Medians (`bench_sky` 50 warmup / 80 iterations)**:
  - Development paired rounds ([`v31/README.md`](Development/ptx-patcher/v31/README.md)): **720p `5.75 ms` / 900p `8.42 ms` / 1080p `11.35 ms`** (1080p repeat: `11.12 ms`);
  - Cooler evaluation round ([`性能评估20261029-2000.md`](Development/doc/性能评估20261029-2000.md)): **720p `5.62 ms` / 900p `8.38 ms` / 1080p `11.07 ms`** (compared with historical `v0.2.0` `6.66 / 9.70 / 12.78 ms`).
  - Benchmark PSNR vs `V2.9_fast`: **`61.738 / 60.821 / 59.645 dB`** (all finite, 0 sky sign flips). All three Windows Feature 18 smokes and both OptiScaler FFX→NGX→NR smokes passed (`nonfinite=0`).
- **Release Packages & Checksums ([`v030/README.md`](Development/ptx-patcher/release-rtx30/v030/README.md))**:
  - `OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip` (`375,029,334` B): `5cd5b76df4287ab7a8c52a81f45fd701fcb053d81bc4b8c4a044afcb43cab470`
  - `OptiScaler-DLSS5-RTX30-0.3.0.zip` (`317,957,671` B): `cb36b3ebd4a4f5413ea814a3138302e5a71ddf4259dbdc0ff8b23f092f0ea573`
  - `Magpie-DLSS5-RTX30-0.3.0.zip` (`322,882,553` B): `46aff5aa9b64ec588779ac52aa7133acfd920a1f2656b786265344598abbb46e`
  - Core DLL SHA256: `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`.

## 0.2.0 (2026-10-26)

Download: [Gofile Mirror](https://gofile.io/d/OOeOcxn6)

All three packages use PTX V2.1: lane-local even/odd K16, selective maxnreg255 in FB00/03/04/05/06, 15/15 O4 in original slots. Model GPU medians: **6.66 / 9.70 / 12.78 ms**. V2.1 is bitwise identical to V2; stack spill falls substantially.

Onimusha root and `_storage_` restore original dxgi and replace the HIP route with PTX (**43 FPS** at 2K Performance on RTX 3080 Laptop, up from `30 FPS` in `v0.1.0`). Stellar Blade and standard OptiScaler default to 1.0/1.0 (with optional `OptiScaler-增强风格.ini` at 1.5/1.1), reaching **nearly 60 FPS** at 2K Performance. Magpie retains its Preset 2 patch.

Historical time ratios versus 0.1.0: about 2.38–2.53×; versus upstream O1: 5.58/5.14/5.30× by tier. All three Feature 18 smokes and both OptiScaler FFX→NGX→NR smokes passed with finite output; ZIP CRC and all file SHA checks passed.

- `OptiScaler-REFramework-DLSS5-RTX30-0.2.0.zip`（375,533,391 B）：`531179b60d55e7147262e488afa760f8fc6422b353882ee5b223c47db3022d94`
- `OptiScaler-DLSS5-RTX30-0.2.0.zip`（318,461,731 B）：`ce7c18e05e286f17b93ee841d2ea9ae829f62cb0a5b3018b93500d3eb902509f`
- `Magpie-DLSS5-RTX30-0.2.0.zip`（323,386,599 B）：`e88a6c86ee6803de64cf6cabb1d3d2af3ef37565c91822a77a5dd8a6ef347739`

Core DLL SHA256: `c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed`.

## 0.1.0 (2026-10-24)

Download: [Gofile Mirror](https://gofile.io/d/s9cpHYH9)

Initial public release for NVIDIA RTX 30 Series GPUs (Ampere `sm_86`), retaining the lightweight **31-block `0.5x Small` model (`Preset 2`)** from `310.9.16.0` and unifying all three release packages onto the **15/15 full-`O4` PTX rewrite route**.

### 1. Full-`O4` PTX Patcher & Hardware Algebraic Identities (`Development/ptx-patcher/`)
- **Fixed `fence.acquire.gpu;` Compilation Failure on `310.9.16.0`**: Lowered both `fence.acquire.gpu;` (newly introduced in Fatbin 5 `cc_vit_1d_*` kernels) and `fence.release.gpu;` to `fence.acq_rel.gpu;` for `sm_86`.
- **Two IEEE 754 `f16x2` Hardware Algebraic Identities (`0 bit-diff` Across Finite Domain)**:
  - `E4M3x2 → FP16x2`: Byte permutation via `prmt.b32` followed by a single hardware `mul.rn.f16x2 %d, %d, 0x5c005c00` ($\times 256.0_{\text{f16}}$), normalizing subnormals and shifting normal exponents in hardware across all 254 finite E4M3 codes;
  - `FP16x2 → E4M3x2`: Exploits $\text{ULP}(2.0_{\text{f16}}) = 2^{-9}$ matching the exact E4M3 subnormal grid spacing via a single `add.rn.f16x2 sub2, sub_in, 0x40004000`, verified with 0 mismatches across all 63,488 finite FP16 values on GPU.
- **15/15 In-Place `O4` Compilation**: Reduced `.cubin` size from `6.7–8.5 MB` to `2.1–2.8 MB`, enabling all 15 Fatbins to compile at `--opt-level=4` and fit directly into their original PE slots (**`2.08×–2.35×` faster** than upstream `O1` fallback).

### 2. Fixed Upstream `fp8_pack_sources` Multi-Definition Bug (Eliminated 106 Sky Bands, `Development/ptx-patcher/sky-audit/`)
- **Root Cause**: Upstream `fp8_pack_sources` ignored braced vector loads (such as `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]` in Fatbin 5 `cc_vit_attention_fp8`) and treated `%r1352` as uniquely defined by the out-of-bounds fallback `mov.b32 %r1352, {%rs2, %rs2}`, replacing live global-memory features with fallback constants and producing 106 periodic red/green horizontal bands on smooth sky gradients.
- **Fix**: Counted destination definitions across all instructions in each `.entry` (including braced vector destinations) and rejected `mapped` forwarding whenever the pack destination, intermediate `.b16`, or source `.b32` register has multiple definitions.
- **Result**: Row-wise R-G sign flips on `1280×720` smooth sky gradients dropped from **`106` to `0`** (high-frequency chroma RMS reduced by 263× from `0.026994` to `0.0001027`), while maintaining full `O4` speed (`15.83 ms` at 720p, `24.47 ms` at 900p, `32.04 ms` at 1080p).

### 3. Release Packages & Checksums
- **`OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`** (`376,272,150 B`, SHA256 `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67`):
  - For Capcom RE Engine games (*Onimusha: Way of the Sword*, *Resident Evil 9*);
  - Includes `dinput8.dll` (REFramework), `dxgi.dll` (OptiScaler), `nvngx.dll_dlssnr.dll`, and full-`O4` `nvngx_dlssnr.dll` (SHA256 `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`);
  - Defaults to `Preset=2, Style=1, WhitePointSource=1`. In *Onimusha*, model GPU time is `7.3–9.1 ms` at 480p (**46 FPS** in-game) and `16.7–17.5 ms` at 720p (**30 FPS** in-game).
- **`OptiScaler-DLSS5-RTX30-0.1.0.zip`** (`319,200,566 B`, SHA256 `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac`):
  - For standard DX12 games (*Stellar Blade*, etc.);
  - Bundles complete FFX loader/upscaler DLLs to support both native DLSS and FSR-to-DLSS input redirection, with single-pass enhanced defaults (`TransferStrength=1.5, ColourStrength=1.1`).
- **`Magpie-DLSS5-RTX30-0.1.0.zip`** (`324,124,886 B`, SHA256 `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb`):
  - For windowed games (*Halo* 720p window → 4K fullscreen);
  - Uses Magpie's native `DLSSNR\DLSSNR_AI_Filter` (Feature 18) + `DLSS\DLSS_SR` pipeline with a binary-patched `Magpie.exe` (`Preset 2`, SHA256 `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea`) and bundled `nvngx_dlss.dll`;
  - 720p `DLSSNR` GPU time is **`15.87–16.00 ms`** (`21.2 ms` total GPU time including 4K `DLSS_SR`).

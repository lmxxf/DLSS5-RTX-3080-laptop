# Changelog

[中文说明](CHANGELOG.zh-CN.md) · [Back to README](README.md)

This file documents the detailed changes, benchmark numbers, configuration options, and SHA256 checksums for each release.

---

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
  - Reduces 720p `DLSSNR` GPU time from `49.8 ms` (Route A) down to **`15.87–16.00 ms`** (`21.2 ms` total GPU time including 4K `DLSS_SR`).

### 4. Additional Route Archive (`Development/hip-port/`)
- Preserved the complete 40-module (1,970-kernel) standalone HIP/CUDA engine ported from AMD RDNA4 (`gfx1201`) to Ampere `sm_86` (V6 8-byte activation pre-shuffling + 32/32 zero-`LMem` kernels, achieving `43.10 ms` at 900p and `57.13 ms` at 1080p).

# DLSS5@NVIDIA RTX 30 (Ampere `sm_86`)

Running NVIDIA DLSS 5 (`nvngx_dlssnr.dll` `310.9.16.0` **31-block Small Neural Rendering model**, "DLSSNR") at full speed on **NVIDIA GeForce RTX 3080 Laptop / RTX 30 Series (Ampere `sm_86`)**.

[中文说明](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Working Plan](Development/WorkingPlan.md) · [Development History](Development/DevHistory.md)

> 🔗 **Sister project for AMD Radeon RX 9070 XT / RDNA 4 (`gfx1201`/`gfx1200`): [dlss5-on-amd-9070xt-porting](https://github.com/lmxxf/dlss5-on-amd-9070xt-porting)** — our original from-scratch HIP re-implementation of NVIDIA's DLSS 5 neural renderer on AMD RDNA 4 GPUs (`2.99 ms` at 720p, `4.25 ms` at 900p, `5.49 ms` at 1080p).

We extract the 15 embedded Fatbin PTX modules from NVIDIA's `nvngx_dlssnr.dll` (`310.9.16.0`), lower Ada/Blackwell-exclusive hardware FP8 (`e4m3x2`) conversions, FP8 `m16n8k32` Tensor Core instructions, and asynchronous barriers into native Ampere `sm_86` PTX, and compress the generated `.cubin` size by **3.5×** using two **IEEE 754 `f16x2` hardware algebraic identities**. This allows **all 15/15 Fatbins to compile at full `--opt-level=4` (`O4`) and fit directly into their original PE slots**—achieving a **`2.08×–2.35×` speedup** over upstream `dev-camo/dlssnr-patcher` (which balloons code size with 48-line integer bit-manipulation sequences and falls back to `O1`), while fixing an upstream `fp8_pack_sources` multi-definition bug that caused 106 periodic red/green horizontal bands across smooth sky gradients. For RTX 30 GPUs, we retain only the lightweight 31-block `0.5x Small` model (`Preset 2`). No NVIDIA binaries or weights are distributed in this repository.

All three release packages share the same pipeline: **capture a frame at the game's (low) render resolution → run our full-`O4` `sm_86` `nvngx_dlssnr.dll` neural renderer → upscale to display resolution via DLSS Super Resolution.**

| Package | Target | Integration Route |
|---|---|---|
| **OptiScaler** (Regular) | Standard DX12 games (*Stellar Blade*, etc.) | OptiScaler intercepts the game's DLSS or FSR inputs, invokes our patched `nvngx_dlssnr.dll` via `nvngx.dll_dlssnr.dll` before SR, and upscales via DLSS SR |
| **OptiScaler-REFramework** (RE Engine) | Capcom RE Engine titles (*Onimusha: Way of the Sword*, *Resident Evil 9*) | Adds REFramework (`dinput8.dll`) on top of the regular OptiScaler package to bypass anti-tamper checks and load `dxgi.dll` |
| **Magpie** (Portable Window Scaler) | Any windowed game (*Halo*, etc.) without built-in DLSS/FSR | Magpie captures the game window (e.g., 720p), runs its native `DLSSNR` (`Preset 2`) filter against our `nvngx_dlssnr.dll`, and upscales to 4K via `DLSS_SR` |

**Current release: 0.3.0 (2026-10-29), PTX V3.1_pack5.** Three official ZIPs have been built and verified locally; a v0.3.0 public mirror has not been uploaded/verified in this release task. 31-block Small / Preset 2 / Style 1, 15/15 O4 in original slots, 266,414,592 bytes.

RTX 3080 Laptop model-only GPU medians (50 warmup / 80 iterations): **development paired rounds 5.75 / 8.42 / 11.35 ms** (1080p repeat: 11.12 ms); a separate cooler run measured **5.62 / 8.38 / 11.07 ms**. Historical v0.2.0: 6.66 / 9.70 / 12.78 ms. These are separate runs under DVFS, not game FPS or a new paired v0.2.0 speedup test. This release changes rounding: benchmark PSNR vs V2.9_fast is **61.738 / 60.821 / 59.645 dB**, not bit-exact. Default OptiScaler strengths remain **1.0/1.0**, with optional **1.5/1.1**. [Release receipt](Development/ptx-patcher/release-rtx30/v030/README.md).

### v0.3.0 checksums

`nvngx_dlssnr.dll` SHA256: `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`

| ZIP | SHA256 |
|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip` | `5cd5b76df4287ab7a8c52a81f45fd701fcb053d81bc4b8c4a044afcb43cab470` |
| `OptiScaler-DLSS5-RTX30-0.3.0.zip` | `cb36b3ebd4a4f5413ea814a3138302e5a71ddf4259dbdc0ff8b23f092f0ea573` |
| `Magpie-DLSS5-RTX30-0.3.0.zip` | `46aff5aa9b64ec588779ac52aa7133acfd920a1f2656b786265344598abbb46e` |


---

## Requirements & Installation

- **Hardware & Driver**: NVIDIA RTX 30 Series GPU (Ampere `sm_86`, tested on RTX 3080 Laptop GPU 16GB; desktop RTX 3060–3090 Ti share `sm_86`) and a standard NVIDIA driver with NGX support (tested on `616.92`). No CUDA Toolkit or Windows Developer Mode is required.
- **Installation**:
  1. **Standard DX12 Games (`OptiScaler-DLSS5-RTX30-0.3.0.zip`)**:
     Close the game. Extract **all files** into the directory containing the actual game `.exe` (e.g., `StellarBlade\SB\Binaries\Win64\`; back up the game's original `amd_fidelityfx_dx12.dll` first, and make sure to extract all companion FFX/XeSS DLLs). Enable DLSS or FSR in game settings.
  2. **Capcom RE Engine Games (`OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip`)**:
     Extract all files into the game `.exe` directory (e.g., `C:\XboxGames\Onimusha- Way of the Sword\Content\`). Enable DLSS in game settings.
  3. **Magpie Window Scaling (`Magpie-DLSS5-RTX30-0.3.0.zip`)**:
     Extract to a standalone folder and run the game in windowed mode (e.g., `1280×720` or `1600×900`). Launch `Magpie.exe` as Administrator, select the default **`DLSS5-RTX30-PTX`** profile (`DLSSNR [Preset 2, Style 1] → DLSS_SR`), click "Scale after 3s", and focus the game window (or press `Alt+Shift+A`).
- **Hotkeys & Tuning**:
  - **`F6`**: Toggle DLSS 5 Neural Rendering on/off in OptiScaler packages.
  - **`Insert`**: Open the OptiScaler menu (`DLSS Neural Rendering` section) to adjust `Style` (`Standard` / `Natural` / `Cinematic`), `Intensity`, `TransferStrength`, and `ColourStrength`.

---

Standard OptiScaler and the local *Stellar Blade* installation now default to **TransferStrength=1.0 /ColourStrength=1.0** to reduce the contrast jump when the motion mask falls back during camera turns. `OptiScaler-增强风格.ini` offers1.5/1.1. The configuration and API smoke were verified; this phase did not repeat in-game visual testing.

## How the PTX Patcher Works — Architecture & Build Pipeline

### 1. Why Original `nvngx_dlssnr.dll` Fails on RTX 30 & Why Upstream `dlssnr-patcher` Is 2× Slower with Sky Banding

NVIDIA's `nvngx_dlssnr.dll` (`310.9.16.0`) embeds 15 Fatbin containers (each holding an `sm_120` Blackwell SASS ELF and a `.version 9.1` PTX source). Ampere (`sm_86`) lacks native hardware instructions for `e4m3x2` conversions, `mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16`, TMA `cp.async.bulk`, and `fence.acquire.gpu;`.

Upstream `dev-camo/dlssnr-patcher` suffers from three critical issues on `310.9.16.0`:
1. **Unhandled `fence.acquire.gpu;`** in Fatbin 5 (`cc_vit_1d_*` kernels), causing `nvptxcompile` to abort on `sm_86`;
2. **48-Line Bitwise Expansion Forcing `O1` Fallback (2× Slowdown)**: Expanding every `cvt.rn.f16x2.e4m3x2` and `cvt.rn.satfinite.e4m3x2.f16x2` into 45–48 lines of integer bit-twiddling inflates `.cubin` sizes to `6.7–8.5 MB`, overflowing the PE Fatbin slots and forcing Fatbins 00–06 down to `--opt-level=1` (`O1`);
3. **Multi-Definition Aliasing in `fp8_pack_sources` (`mapped` Shortcut) Causing 106 Red/Green Sky Bands**: Upstream replaces an `mma.sync` operand `%r` with its pre-conversion FP16 registers whenever `%r` appears only once in `FP8_PACK_PATTERN` (`mov.b32 %r, {%rs1, %rs2}`). However, in kernels such as `cc_vit_attention_fp8` (Fatbin 5), `%r1352` is loaded from global memory in the in-bounds branch via braced vector load `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]`, and only assigned `mov.b32 %r1352, {%rs2, %rs2}` in the out-of-bounds fallback branch. Upstream missed the vector load definition and unconditionally replaced `%r1352` with the out-of-bounds fallback constant, producing 106 periodic red/green horizontal bands across smooth sky gradients.

### 2. Our Five Core Improvements ([`Development/ptx-patcher/build_sm86_dlls.py`](Development/ptx-patcher/build_sm86_dlls.py))

1. **Identity 1 (`E4M3x2 → FP16x2` in 4 SASS Instructions, `0 bit-diff` Across All 254 Finite Values)**:
   Since the exponent bias difference between FP16 ($15$) and E4M3 ($7$) is $8$, placing two E4M3 bytes into the high/low 16-bit halves via `prmt.b32`, separating the sign bit, and shifting the 7-bit payload right by 1 bit aligns it to FP16 `bit [13:7]` (forming an unscaled FP16 normal for $e \ge 1$ and an FP16 subnormal $(-1)^s \cdot 2^{-14} \cdot (m/8)$ for $e = 0$). A single hardware **`mul.rn.f16x2 %d, %d, 0x5c005c00;`** ($\times 2^8 = 256.0_{\text{f16}}$) normalizes subnormals and adjusts normal exponents in hardware with zero branches.
2. **Identity 2 (`FP16x2 → E4M3x2` Hardware Subnormal RNE Rounding, `0 bit-diff` Across All 63,488 Finite Values)**:
   In IEEE FP16, $\text{ULP}(2.0_{\text{f16}}) = 2^1 \times 2^{-10} = 2^{-9}$, which matches the exact E4M3 subnormal grid spacing $2^{-9}$. Executing **`add.rn.f16x2 sub2, sub_in, 0x40004000;`** (`+2.0h`) performs hardware Round-to-Nearest-Even on both subnormal lanes simultaneously, placing the 3-bit subnormal mantissas directly in the low bytes of `sub2`.
   Together, these two identities shrink `.cubin` sizes by 3.5× (`2.1–2.8 MB`), allowing **all 15/15 Fatbins to compile at full `O4` and fit in place**.
3. **Whole-Entry Multi-Definition Filtering (`106 → 0` Sky Bands)**:
   We parse all destination operands across every instruction in each `.entry` (including braced vector loads `{ %r1, ... }`) and reject `mapped` forwarding whenever the pack destination, intermediate `.b16`, or source `.b32` register has multiple definitions, eliminating all 106 sky bands while preserving full `O4` speed.

4. **Lane-local even/odd K16 split**: A/B use the same K permutation: bytes0/2 then1/3. Encoded operands need no lane SHFL or PRMT; valid mapped values use5410/7632 PRMT. FP16 accumulation grouping changes. V2.1 is bitwise identical to V2, not to0.1.0.
5. **Selective register caps**: raise existing `.maxnreg` to255 only in FB00/03/04/05/06. Keep FB01/02 unchanged. STACK and LDL/STL reach zero in FB00/03/06; FB04/05 retain maximum80/8B STACK. The all255 control was slower, so the measured hot255 profile is released.

### Current v0.3.0 implementation

V2.2 added native `cp.async.mbarrier.arrive` completion and branchless SWAR pack. V2.3 introduced the 8-instruction even/odd PRMT decode; V2.6 switched to Low/High selectors **0x9180/0xb3a2** and direct mapped halves (21,712 generated mapped PRMT sites removed). V2.4 introduced just-in-time decode and dead temporary reuse. V2.7 caps only four C32 kernels at168 to increase theoretical residency from8 to12 warps/SM. V2.9→V3.1 unifies normal/subnormal alignment with half2 ×2^-8, folds abs into HMNMX2, and uses LEA rounding toward zero at ties: pair pack core13→9→5 SASS. The 38-active-kernel non-NOP total is152,076 (V2.9_fast163,944). This is a static count, not executed instructions per frame; remaining spill is not zero.

Release-specific source and commands: [V3.1](Development/ptx-patcher/v31/README.md), [v0.3.0 packaging](Development/ptx-patcher/release-rtx30/v030/README.md). Generic commands below reproduce historical stages and do not implicitly select the current release.

### 3. Build Commands

```bash
# 1. Patch nvngx_dlssnr.dll (310.9.16.0, SHA256: 2bc19bc0...) to full-O4 sm_86
python3 Development/ptx-patcher/build_sm86_dlls.py \
  --input /path/to/original/nvngx_dlssnr.dll \
  --output /path/to/output/nvngx_dlssnr.dll \
  --maxnreg 0:255 --maxnreg 3:255 --maxnreg 4:255 \
  --maxnreg 5:255 --maxnreg 6:255 --workers 3

# 2. Patch Magpie.exe (0.6.6) to use Preset 2 (31-block Small model) instead of hardcoded Preset 0
python3 Development/ptx-patcher/magpie-native/patch_preset2.py \
  --input /path/to/original/Magpie.exe \
  --output /path/to/output/Magpie.exe

# 3. Run unit & regression tests
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

---

## Benchmark Comparison (RTX 3080 Laptop GPU, 16GB, `sm_86`)

| Approach (31-Block `0.5x Small`, `Preset 2`) | Compiler Opt | `1280×720` (720p) | `1600×900` (900p) | `1920×1080` (1080p) | Sky R-G Sign Flips | Speedup vs. Upstream |
|---|:---:|---:|---:|---:|---:|:---:|
| ① Upstream `dlssnr-patcher` (`stock`) | Forced `O1` | `37.13 ms` | `49.89 ms` | `67.69 ms` | `106` (severe banding) | `1.00×` |
| **② Our `ptx-patcher` (`v0.1.0`)** | **15/15 Full `O4`** | **`15.83 ms`** | **`24.47 ms`** | **`32.04 ms`** | **`0` (band-free)** | **`2.08× ～ 2.35×`** |
| **③ Historical `ptx-patcher` (`v0.2.0 / V2.1`)** | **15/15 `O4` + 0-SHFL + `255` Regs** | **`6.66 ms`** | **`9.70 ms`** | **`12.78 ms`** | **`0` (band-free)** | **`5.14× ～ 5.58×`** |
| **④ Current `v0.3.0 / V3.1_pack5`** | **15/15 O4, Low/High K16, 5-SASS pack** | **5.75 ms** | **8.42 ms** | **11.35 ms** | **0 (tested sky)** | Separate-run history; no new paired upstream claim |

---

## Release History

Detailed release notes are maintained in [CHANGELOG.md](CHANGELOG.md).

| Version | Date | Highlights | Results |
|---|---|---|---|
| **`0.3.0`** | 2026-10-29 | PTX V3.1_pack5; Low/High mapped forwarding, asynchronous completion, pooled decoding, four C32 caps, 5-SASS approximate pack. Local three-package validation complete. | Model medians **5.75 / 8.42 / 11.35 ms**, separate cooler run5.62/8.38/11.07. [Receipt](Development/ptx-patcher/release-rtx30/v030/README.md) |
| **`0.2.0`** | 2026-10-26 | Lane-local even/odd K16 + selective maxnreg255; standard defaults 1.0/1.0 with optional 1.5/1.1; three new ZIPs and checksums ([Gofile](https://gofile.io/d/OOeOcxn6)). | **6.66 / 9.70 / 12.78 ms**; *Onimusha* 2K Perf **43 FPS** (up from 30 FPS), *Stellar Blade* 2K Perf **~60 FPS**. [Receipt](Development/ptx-patcher/release-rtx30/v020/README.md) |
| **`0.1.0`** | 2026-10-24 | Initial release unifying all three packages (`OptiScaler-REFramework`, `OptiScaler`, `Magpie`) onto the **15/15 full-`O4` PTX route (`Preset 2` 31-block Small model)**; IEEE 754 `f16x2` hardware conversion identities; multi-definition `mapped` fix eliminating 106 sky bands; native Magpie `Preset 2` binary patch (`15.9 ms`). | 720p **`15.83 ms`**, 900p **`24.47 ms`**, 1080p **`32.04 ms`**; verified in *Onimusha*, *Stellar Blade*, and *Halo* (Magpie) |

---

## Repository Structure

| Path | Description |
|---|---|
| `Development/ptx-patcher/` | Full-`O4` `sm_86` PTX patcher (`build_sm86_dlls.py`, `dlssnr_patcher.py`), NGX caller forwarder (`dlssnr_forwarder.cpp`), D3D12 NGX benchmark (`bench_nvngx.dll.cpp`), sky banding audit (`sky-audit/`), zero-shuffle & register tuning (`v2/`, `v21/`), Magpie native `Preset 2` patcher (`magpie-native/`), and release packaging scripts (`release-rtx30/`) |
| `Development/doc/` | User guides and technical notes ([`改进和使用说明_0.2.0.md`](Development/doc/改进和使用说明_0.2.0.md), [`使用说明.md`](Development/doc/使用说明.md)) |
| `Development/DevHistory.md` | Complete engineering log, ablation tables, and SHA256 receipts |
| `Development/WorkingPlan.md` | Architecture overview and active roadmap |
| `CHANGELOG.md` / `CHANGELOG.zh-CN.md` | Detailed per-release changelog |

---

## License

Code in this repository is released under the [MIT License](LICENSE). NVIDIA binaries and model weights are not distributed.

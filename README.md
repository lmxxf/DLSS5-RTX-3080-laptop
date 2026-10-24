# DLSS5@NVIDIA RTX 30 (Ampere `sm_86`)

Running NVIDIA DLSS 5 (`nvngx_dlssnr.dll` `310.9.16.0` **31-block Small Neural Rendering model**, "DLSSNR") at full speed on **NVIDIA GeForce RTX 3080 Laptop / RTX 30 Series (Ampere `sm_86`)**.

[中文说明](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Working Plan](Development/WorkingPlan.md) · [Development History](Development/DevHistory.md)

We extract the 15 embedded Fatbin PTX modules from NVIDIA's `nvngx_dlssnr.dll` (`310.9.16.0`), lower Ada/Blackwell-exclusive hardware FP8 (`e4m3x2`) conversions, FP8 `m16n8k32` Tensor Core instructions, and asynchronous barriers into native Ampere `sm_86` PTX, and compress the generated `.cubin` size by **3.5×** using two **IEEE 754 `f16x2` hardware algebraic identities**. This allows **all 15/15 Fatbins to compile at full `--opt-level=4` (`O4`) and fit directly into their original PE slots**—achieving a **`2.08×–2.35×` speedup** over upstream `dev-camo/dlssnr-patcher` (which balloons code size with 48-line integer bit-manipulation sequences and falls back to `O1`), while fixing an upstream `fp8_pack_sources` multi-definition bug that caused 106 periodic red/green horizontal bands across smooth sky gradients. For RTX 30 GPUs, we retain only the lightweight 31-block `0.5x Small` model (`Preset 2`). No NVIDIA binaries or weights are distributed in this repository.

All three release packages share the same pipeline: **capture a frame at the game's (low) render resolution → run our full-`O4` `sm_86` `nvngx_dlssnr.dll` neural renderer → upscale to display resolution via DLSS Super Resolution.**

| Package | Target | Integration Route |
|---|---|---|
| **OptiScaler** (Regular) | Standard DX12 games (*Stellar Blade*, etc.) | OptiScaler intercepts the game's DLSS or FSR inputs, invokes our patched `nvngx_dlssnr.dll` via `nvngx.dll_dlssnr.dll` before SR, and upscales via DLSS SR |
| **OptiScaler-REFramework** (RE Engine) | Capcom RE Engine titles (*Onimusha: Way of the Sword*, *Resident Evil 9*) | Adds REFramework (`dinput8.dll`) on top of the regular OptiScaler package to bypass anti-tamper checks and load `dxgi.dll` |
| **Magpie** (Portable Window Scaler) | Any windowed game (*Halo*, etc.) without built-in DLSS/FSR | Magpie captures the game window (e.g., 720p), runs its native `DLSSNR` (`Preset 2`) filter against our `nvngx_dlssnr.dll`, and upscales to 4K via `DLSS_SR` |

**Current Release: 0.1.0 (2026-10-24).** Download: [Gofile Mirror](https://gofile.io/d/s9cpHYH9). Initial release unifying all three packages onto the **15/15 full-`O4` PTX rewrite route (`Preset 2` 31-block Small model)**. Fixes `fence.acquire.gpu;` compilation failure on `310.9.16.0`, eliminates `O1` performance degradation, and resolves the 106-band sky artifact caused by `fp8_pack_sources` multi-definition aliasing. On RTX 3080 Laptop (132W), single-frame model GPU time is **`15.83 ms` at 720p, `24.47 ms` at 900p, and `32.04 ms` at 1080p (`8.2 ms` at 480p)**. See [full release notes](CHANGELOG.md#010-2026-10-24).

---

## Requirements & Installation

- **Hardware & Driver**: NVIDIA RTX 30 Series GPU (Ampere `sm_86`, tested on RTX 3080 Laptop GPU 16GB; desktop RTX 3060–3090 Ti share `sm_86`) and a standard NVIDIA driver with NGX support (tested on `616.92`). No CUDA Toolkit or Windows Developer Mode is required.
- **Installation**:
  1. **Standard DX12 Games (`OptiScaler-DLSS5-RTX30-0.1.0.zip`)**:
     Close the game. Extract **all files** into the directory containing the actual game `.exe` (e.g., `StellarBlade\SB\Binaries\Win64\`; back up the game's original `amd_fidelityfx_dx12.dll` first, and make sure to extract all companion FFX/XeSS DLLs). Enable DLSS or FSR in game settings.
  2. **Capcom RE Engine Games (`OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`)**:
     Extract all files into the game `.exe` directory (e.g., `C:\XboxGames\Onimusha- Way of the Sword\Content\`). Enable DLSS in game settings.
  3. **Magpie Window Scaling (`Magpie-DLSS5-RTX30-0.1.0.zip`)**:
     Extract to a standalone folder and run the game in windowed mode (e.g., `1280×720` or `1600×900`). Launch `Magpie.exe` as Administrator, select the default **`DLSS5-RTX30-PTX`** profile (`DLSSNR [Preset 2, Style 1] → DLSS_SR`), click "Scale after 3s", and focus the game window (or press `Alt+Shift+A`).
- **Hotkeys & Tuning**:
  - **`F6`**: Toggle DLSS 5 Neural Rendering on/off in OptiScaler packages.
  - **`Insert`**: Open the OptiScaler menu (`DLSS Neural Rendering` section) to adjust `Style` (`Standard` / `Natural` / `Cinematic`), `Intensity`, `TransferStrength`, and `ColourStrength`.

---

## How the PTX Patcher Works — Architecture & Build Pipeline

### 1. Why Original `nvngx_dlssnr.dll` Fails on RTX 30 & Why Upstream `dlssnr-patcher` Is 2× Slower with Sky Banding

NVIDIA's `nvngx_dlssnr.dll` (`310.9.16.0`) embeds 15 Fatbin containers (each holding an `sm_120` Blackwell SASS ELF and a `.version 9.1` PTX source). Ampere (`sm_86`) lacks native hardware instructions for `e4m3x2` conversions, `mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16`, TMA `cp.async.bulk`, and `fence.acquire.gpu;`.

Upstream `dev-camo/dlssnr-patcher` suffers from three critical issues on `310.9.16.0`:
1. **Unhandled `fence.acquire.gpu;`** in Fatbin 5 (`cc_vit_1d_*` kernels), causing `nvptxcompile` to abort on `sm_86`;
2. **48-Line Bitwise Expansion Forcing `O1` Fallback (2× Slowdown)**: Expanding every `cvt.rn.f16x2.e4m3x2` and `cvt.rn.satfinite.e4m3x2.f16x2` into 45–48 lines of integer bit-twiddling inflates `.cubin` sizes to `6.7–8.5 MB`, overflowing the PE Fatbin slots and forcing Fatbins 00–06 down to `--opt-level=1` (`O1`);
3. **Multi-Definition Aliasing in `fp8_pack_sources` (`mapped` Shortcut) Causing 106 Red/Green Sky Bands**: Upstream replaces an `mma.sync` operand `%r` with its pre-conversion FP16 registers whenever `%r` appears only once in `FP8_PACK_PATTERN` (`mov.b32 %r, {%rs1, %rs2}`). However, in kernels such as `cc_vit_attention_fp8` (Fatbin 5), `%r1352` is loaded from global memory in the in-bounds branch via braced vector load `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]`, and only assigned `mov.b32 %r1352, {%rs2, %rs2}` in the out-of-bounds fallback branch. Upstream missed the vector load definition and unconditionally replaced `%r1352` with the out-of-bounds fallback constant, producing 106 periodic red/green horizontal bands across smooth sky gradients.

### 2. Our Three Core Improvements ([`Development/ptx-patcher/build_sm86_dlls.py`](Development/ptx-patcher/build_sm86_dlls.py))

1. **Identity 1 (`E4M3x2 → FP16x2` in 4 SASS Instructions, `0 bit-diff` Across All 254 Finite Values)**:
   Since the exponent bias difference between FP16 ($15$) and E4M3 ($7$) is $8$, placing two E4M3 bytes into the high/low 16-bit halves via `prmt.b32`, separating the sign bit, and shifting the 7-bit payload right by 1 bit aligns it to FP16 `bit [13:7]` (forming an unscaled FP16 normal for $e \ge 1$ and an FP16 subnormal $(-1)^s \cdot 2^{-14} \cdot (m/8)$ for $e = 0$). A single hardware **`mul.rn.f16x2 %d, %d, 0x5c005c00;`** ($\times 2^8 = 256.0_{\text{f16}}$) normalizes subnormals and adjusts normal exponents in hardware with zero branches.
2. **Identity 2 (`FP16x2 → E4M3x2` Hardware Subnormal RNE Rounding, `0 bit-diff` Across All 63,488 Finite Values)**:
   In IEEE FP16, $\text{ULP}(2.0_{\text{f16}}) = 2^1 \times 2^{-10} = 2^{-9}$, which matches the exact E4M3 subnormal grid spacing $2^{-9}$. Executing **`add.rn.f16x2 sub2, sub_in, 0x40004000;`** (`+2.0h`) performs hardware Round-to-Nearest-Even on both subnormal lanes simultaneously, placing the 3-bit subnormal mantissas directly in the low bytes of `sub2`.
   Together, these two identities shrink `.cubin` sizes by 3.5× (`2.1–2.8 MB`), allowing **all 15/15 Fatbins to compile at full `O4` and fit in place**.
3. **Whole-Entry Multi-Definition Filtering (`106 → 0` Sky Bands)**:
   We parse all destination operands across every instruction in each `.entry` (including braced vector loads `{ %r1, ... }`) and reject `mapped` forwarding whenever the pack destination, intermediate `.b16`, or source `.b32` register has multiple definitions, eliminating all 106 sky bands while preserving full `O4` speed.

### 3. Build Commands

```bash
# 1. Patch nvngx_dlssnr.dll (310.9.16.0, SHA256: 2bc19bc0...) to full-O4 sm_86
python3 Development/ptx-patcher/build_sm86_dlls.py \
  --input /path/to/original/nvngx_dlssnr.dll \
  --output /path/to/output/nvngx_dlssnr.dll \
  --workers 3

# 2. Patch Magpie.exe (0.6.6) to use Preset 2 (31-block Small model) instead of hardcoded Preset 0
python3 Development/ptx-patcher/magpie-native/patch_preset2.py \
  --input /path/to/original/Magpie.exe \
  --output /path/to/output/Magpie.exe

# 3. Run unit & regression tests
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

---

## Benchmark & In-Game Results (RTX 3080 Laptop GPU, 16GB, `sm_86`, 132W)

| Approach (31-Block `0.5x Small`, `Preset 2`) | Compiler Opt | `1280×720` (720p) | `1600×900` (900p) | `1920×1080` (1080p) | Sky R-G Sign Flips | Speedup vs. Upstream |
|---|:---:|---:|---:|---:|---:|:---:|
| ① Upstream `dlssnr-patcher` (`stock`) | Forced `O1` | `37.13 ms` | `49.89 ms` | `67.69 ms` | `106` (severe banding) | `1.00×` |
| ② Standalone CUDA Engine (`hip-port`) | `Clang O3 + O4` | `~31.0 ms` | `43.10 ms` | `57.13 ms` | `0` | `1.18×` |
| **③ Our `ptx-patcher` (`v0.1.0`)** | **15/15 Full `O4`** | **`15.83 ms`** | **`24.47 ms`** | **`32.04 ms`** | **`0` (band-free)** | **`2.08× ～ 2.35×`** |

---

## Release History

Detailed release notes are maintained in [CHANGELOG.md](CHANGELOG.md).

| Version | Date | Highlights | Results |
|---|---|---|---|
| **`0.1.0`** | 2026-10-24 | Initial release unifying all three packages (`OptiScaler-REFramework`, `OptiScaler`, `Magpie`) onto the **15/15 full-`O4` PTX route (`Preset 2` 31-block Small model)**; IEEE 754 `f16x2` hardware conversion identities; multi-definition `mapped` fix eliminating 106 sky bands; native Magpie `Preset 2` binary patch (`49.8 ms → 15.9 ms`). | 720p **`15.83 ms`**, 900p **`24.47 ms`**, 1080p **`32.04 ms`**; verified in *Onimusha*, *Stellar Blade*, and *Halo* (Magpie) |

---

## Repository Structure

| Path | Description |
|---|---|
| `Development/ptx-patcher/` | **Primary Route (`v0.1.0`)**: Full-`O4` `sm_86` PTX patcher (`build_sm86_dlls.py`, `dlssnr_patcher.py`), NGX caller forwarder (`dlssnr_forwarder.cpp`), D3D12 NGX benchmark (`bench_nvngx.dll.cpp`), sky banding audit (`sky-audit/`), Magpie native `Preset 2` patcher (`magpie-native/`), and release packaging scripts (`release-rtx30/`) |
| `Development/hip-port/` | **Additional / Experimental Route**: Standalone 40-module (1,970-kernel) HIP/CUDA inference engine ported from AMD RDNA4 (`gfx1201`) to Ampere `sm_86` (`hip/sm86_compat.h`, V6 SSA compiler pass `hip/build_sm86_modules.py`, `LmxxfNrRuntime.dll`, and `dlss5-amd.addon64`) |
| `Development/DevHistory.md` | Complete engineering log, ablation tables, and SHA256 receipts |
| `Development/WorkingPlan.md` | Architecture overview and active roadmap |
| `CHANGELOG.md` / `CHANGELOG.zh-CN.md` | Detailed per-release changelog |

---

## License

Code in this repository is released under the [MIT License](LICENSE). NVIDIA binaries and model weights are not distributed.

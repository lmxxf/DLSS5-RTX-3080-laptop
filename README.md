# DLSS5 RTX 3080 Laptop — v0.1.0

Run the **31-block Small NR model** on NVIDIA GeForce RTX 3080 Laptop (Ampere `sm_86`). The current product is [Development/ptx-patcher](Development/ptx-patcher): rewrite the PTX embedded in the original **310.9.16.0 `nvngx_dlssnr.dll`**, keeping **all 15 fatbins at O4 in their original slots**. All three v0.1.0 packages use this route, including Magpie's native Feature 18 backend.

[中文](README.zh-CN.md) · [Working plan](Development/WorkingPlan.md) · [Development history and experimental conditions](Development/DevHistory.md)

## Core changes

### Compact FP8 conversions using IEEE 754 FP16 hardware

Ampere cannot execute this model's E4M3 conversions and FP8 MMA directly. Expanding them into integer code increases cubin size, forcing upstream's main-network fatbins down to O1. This patch uses two `f16x2` identities and lowers FP8 `m16n8k32` to two FP16 `m16n8k16` operations.

1. **E4M3 → FP16:** rearrange the sign/exponent/mantissa bits into FP16, then multiply both lanes by 256 using `mul.rn.f16x2` (`0x5c005c00`). FP16 hardware also normalizes subnormals correctly.
2. **FP16 → E4M3:** FP16's ULP at `2.0h` is `2^-9`, exactly the E4M3 subnormal grid. Adding `2.0h` with `add.rn.f16x2` (`0x40004000`) supplies round-to-nearest-even for that range. Normal values use compact bit packing, with sign and finite saturation preserved.

The conversion helpers are **0 bit-diff over the tested finite domains**: 254 finite E4M3 encodings; GPU round-trip checks cover 63,488 finite FP16 encodings in each packed lane with zero mismatches. See the [GPU conversion check](Development/ptx-patcher/sky-audit/existing-roundtrip-gpu.txt). This is not a whole-model equivalence claim against NVIDIA or upstream, nor a claim about arbitrary NaN payloads.

### Fix invalid mapped operand forwarding

Upstream `fp8_pack_sources` counted specific conversion/pack patterns rather than all definitions. In FB5, `%r1352` is written by both a real vector load and an out-of-bounds fallback pack. Forwarding it from the fallback's FP16 source replaces real input data and creates alternating sky colors.

The production filter counts register definitions across each entry, including scalar destinations, vector braces and inline instructions. It rejects mapped operands when the packed target, FP8 intermediates or FP16 source has multiple definitions. Single-definition cross-block forwarding remains enabled; eligible operands keep the original `shfl + shfl + selp` path **without extra quantization**.

On the same 1280×720 smooth-sky input, the mean row red/green difference went from **106 sign changes to zero**, with high-frequency RMS about `0.0001027`. The number describes sign changes, not complete periods. Subsequent user tests accepted Onimusha and Stellar Blade. Strict same-block filtering and explicit mapped quantization remain slower diagnostic options; the default filter is not a full CFG dominance proof. See the [controlled experiment](Development/ptx-patcher/sky-audit/去量化控制变量回执.md).

## Three v0.1.0 packages

This project's first version is **0.1.0**. **AMD 0.44** identifies the upstream packaging baseline only. Binaries, weights and ZIPs are distributed separately and are not committed to Git. Each archive contains instructions and per-file `SHA256SUMS.txt`; each ZIP has a `.sha256` sidecar.

| Package | Intended use | Default chain |
|---|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip` | Onimusha: Way of the Sword, Resident Evil 9 and RE Engine integrations | NR → DLSS SR; includes REFramework `dinput8.dll` |
| `OptiScaler-DLSS5-RTX30-0.1.0.zip` | Stellar Blade and conventional DX12 integrations | DLSS/FFX input → NR → DLSS SR; no REFramework |
| `Magpie-DLSS5-RTX30-0.1.0.zip` | Window capture without an in-game integration | Native Magpie DLSSNR → DLSS_SR; no ReShade/add-on |

### REFramework package

1. Close the game, back up conflicting mod files, and extract **the entire package** beside the actual game executable. The Xbox Onimusha example is `C:\XboxGames\Onimusha- Way of the Sword\Content\`.
2. Keep `dinput8.dll`, the new 26 MB `dxgi.dll`, `nvngx.dll_dlssnr.dll`, the patched `nvngx_dlssnr.dll`, and the support libraries together. Do not mix in the old independent runtime.
3. Defaults: Preset 2, Style 1, one pass, detail/color `1.0/1.0`, game exposure (`WhitePointSource=1`, `WhitePointTrim=1`). F6 toggles NR; Insert opens OptiScaler.

### Standard OptiScaler package

For Stellar Blade, install beside `SB-Win64-Shipping.exe` in `SB\Binaries\Win64\`. **Back up the game's original `amd_fidelityfx_dx12.dll` first.** Copy all files: the 26 KB FFX loader needs the approximately 28 MB upscaler, XeSS/NvAPI support libraries and `D3D12_Optiscaler`. A four-file installation is insufficient for the complete FFX route.

- `Dx12Upscaler=dlss` selects the output backend. FFX and FSR2/3 inputs are enabled, while `EnableHotSwapping=false` fixes the output route. The game's native DLSS SR runtime and NVIDIA NGX driver must be available.
- The complete Stellar Blade package passed user acceptance. A Windows FFX→NGX→NR smoke test also executed the model. For a particular game's FSR path, check for `reached through the game's FFX input` and NR composition in its log.
- Defaults use detail `1.5`, color `1.1`, still one pass. `OptiScaler-原始平衡.ini` restores `1.0/1.0`. Keep scene and quality mode fixed when comparing with F6.
- At 4K output, FFX queries returned 2560×1440 for Quality, 1920×1080 for Performance and 1280×720 for Ultra Performance. Start with Quality for clarity, then trade resolution for performance.

Stellar Blade's exposure-derived white point is about `1x`; Onimusha's is about `520x`. These are `pre-exposure / game exposure` scales, not effect-strength multipliers. Do not copy one game's number into another.

### Magpie: native PTX, replacing the old CUDA default

Exit other Magpie instances, extract the package and run its `Magpie.exe`. Select **DLSS5-RTX30-PTX** and start the three-second countdown with the target game window in front.

- Native `DLSSNR\DLSSNR_AI_Filter` performs same-size NR at Preset 2 / Style 1, followed by `DLSS\DLSS_SR`. Tested at 1280×720 → 3840×2160.
- Includes `nvngx_dlssnr.dll` and the native SR runtime `nvngx_dlss.dll`. No ReShade `dxgi.dll`, `dlss5-amd.addon64`, or external `DLSS5-AMD/` weights. Remove these old-package leftovers before upgrading.
- The customized Magpie 0.6.6 **hard-codes Preset 0**; JSON cannot select 2. The package has a hash-gated minimal EXE patch changing that parameter call and its status text. Automatic updates are disabled to preserve it. See the [patcher](Development/ptx-patcher/magpie-native/patch_preset2.py) and [manifest](Development/ptx-patcher/magpie-native/preset2-patch.json).
- Magpie already contains signed-snippet/caller-IAT compatibility. Use Magpie's own comparison controls; the old add-on F6 toggle is no longer present. Task switching ends fullscreen scaling.
- The default chain excludes FSR4 and XeSSFG. Missing `nvngx_dlss.dll` reproduced `0xbad0000b`; supplying it fixed D3D11 creation and the actual capture chain.

## Measurements and boundaries

Test machine: Windows 11, RTX 3080 Laptop 16 GB (GA104, 48 SMs, `sm_86`), high-performance operation around 132 W, NVIDIA driver 616.92 in the recorded runs. Other RTX 30 models have not each been validated.

### Historical upstream O1 vs compact O4 comparison

Same 31-block model, Preset 2, D3D12 timestamps; minimum GPU times:

| Implementation | 1600×900 | 1920×1080 |
|---|---:|---:|
| Upstream integer lowering, main-network O1 fallback | 49.89 ms | 67.69 ms |
| Compact conversion, 15/15 O4 | 23.97 ms | 29.97 ms |
| Speedup | **2.08×** | **2.25×** |

These are earlier performance measurements. Both builds then shared invalid mapped forwarding, so their bitwise agreement was not a correctness proof. Later corrected v0.1.0 checks, with five warm-up and twenty measured frames, gave GPU medians of **15.829 ms (720p sky), 24.474 ms (900p original bench scene), and 32.036 ms (1080p original bench scene)**, still with 15/15 O4 in the original slots.

### Games and actual window capture

| Scenario | Recorded result | Scope |
|---|---|---|
| Onimusha, 2K display / internal 480p | NR 7.3–9.1 ms; game about 46 FPS | Earlier integration run |
| Onimusha, 2K display / internal 720p | NR 16.7–17.7 ms; game about 30 FPS | Earlier integration run |
| Onimusha, 4K display / internal 720p | Recent examples: model 17.24–17.35 ms; total NR 17.51–17.68 ms; sky bands accepted as fixed by the user | No additional whole-game FPS recorded for that run |
| Stellar Blade, 4K display / approximately 720p internal | Recent examples: model 18.18–18.62 ms; total NR 18.42–18.86 ms; complete package accepted by the user | No whole-game FPS recorded; 1080p rendering also appears in the log |
| Magpie + Halo, old independent engine, 720p→4K | Median callback interval 49.8 ms, about 20 FPS; Small model / 1344×768 processing surface | Actual user game run, not isolated model GPU time |
| Magpie **native PTX**, animated 720p window→4K | NR GPU window averages **15.868–16.199 ms**; 960 successful evaluations, zero failures | Publication fence including downstream SR/synchronization about 21.1–21.5 ms; observed evaluation cadence about 36 FPS |

**15.9 ms is native Magpie NR GPU time, not a verified 40+ FPS Halo result.** The native route is deployed, but the animation-window test and Halo run are not a same-frame/same-load A/B. See the [native report](Development/ptx-patcher/magpie-native/测试回执.txt) and [log](Development/ptx-patcher/magpie-native/evidence/magpie.log).

## Build and validate

The PTX builder needs Python 3, NumPy, `libzstd.so.1`, and a working NVIDIA CUDA Driver API/JIT in WSL. It currently loads `/usr/lib/wsl/lib/libcuda.so.1`. HIP assets and external model weights are not needed for this route.

Only the original 310.9.16.0 input with this SHA256 is accepted:
`2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f`

```bash
python3 Development/ptx-patcher/build_sm86_dlls.py --input /path/to/original/nvngx_dlssnr.dll --output /path/to/output/nvngx_dlssnr.dll --workers 3
```

Defaults: multi-definition filtering, no additional mapped quantization. `--mapped-mode strict` restricts sources to the same block; add `--quantize-mapped` for the slower quantization control. The builder can append a PE section for oversized O4 fatbins, but **the current release DLL does not need expansion**.

Patch the known Magpie EXE to Preset 2:

```bash
python3 Development/ptx-patcher/magpie-native/patch_preset2.py --input /path/to/original/Magpie.exe --output /path/to/output/Magpie.exe
```

Both input and output EXE hashes are pinned. Other Magpie versions are rejected.

```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

[Release scripts and receipts](Development/ptx-patcher/release-rtx30/) reference local external base packages/runtime paths; adjust them for another machine. `sky-audit` and `magpie-fix` retain chronological experiments and failures, not a second production entry point.

## Artifact hashes

| File | SHA256 |
|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip` | `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67` |
| `OptiScaler-DLSS5-RTX30-0.1.0.zip` | `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac` |
| `Magpie-DLSS5-RTX30-0.1.0.zip` | `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb` |
| Patched `nvngx_dlssnr.dll` | `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a` |
| Preset 2 `Magpie.exe` | `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea` |

## Layout

`Development/` contains only `DevHistory.md`, `WorkingPlan.md`, `ptx-patcher/`, and `hip-port/`.

The PTX implementation, packaging tools, sky diagnostics, native Magpie integration and historical repair evidence all live under `Development/ptx-patcher/`.

## Additional / experimental route

[Development/hip-port](Development/hip-port) retains the RDNA4 Wave32→Ampere independent HIP/CUDA engine: 40 modules, 1,970 entry points and D3D12/CUDA shared-resource interop. It is useful for source research and integrations without a native NR backend, **not the default of any v0.1.0 package**. Historical code still supports the old model; current releases enable only the 31-block Small model.

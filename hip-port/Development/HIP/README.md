# HIP backend development

The HIP branch contains a complete GPU inference backend and an experimental D3D12 bridge/addon. Magpie retains the validated900P HLSL release. On2026-09-15, the user requested and received the experimental HIP candidate in Stellar Blade; rollback instructions are below.

| Path | Verified result | Remaining limitation |
|---|---|---|
| Exact512 graph |786432 RGB float values bitwise equal to original oracle|Offline reference/performance development|
| Exact900 graph |WMMA equals HIP scalar, including pooled execution|Uses original precision schedule, distinct from shipped fast HLSL|
| Production operator families |True HLSL comparisons passed for C32, MH, ViT, split, decoder and pool|Whole fast graph still differs from production output|
| GPU pointer/D3D12 bridge |Complete900 graph round-trips with identical output; temporal frame test passed|Candidate not installed; formal driver not tested|

Exact512 SHA256: `bd52c601b68c4ed27f271cd2c7bcffc8511519f652534f2a0c51ffa9450e6da4`. Latest fast900 offline hot wall time is about70–72ms, with1.9GiB graph allocations. This is slower than the existing HLSL release. Whole fast output RMSE is about0.00927 against the shipped HLSL on the tiled fixture; it is not accepted as production parity. See [DevHistory](../DevHistory.md) for test conditions, failures and later updates.

## Build

[TOOLCHAIN.md](TOOLCHAIN.md) describes the SDKless COMGR compiler. It uses installed Windows COMGR3; headers/device libraries and experimental DirectX are unnecessary for HIP compilation/execution. Tested GPU: RX9070XT/gfx1201; runtime: System32 `amdhip64_7.dll`; driver32.0.31007.2048. HIP6 explicitly failed in a separate attempt, so there is no automatic fallback. Official [HIP SDK release notes](https://rocm.docs.amd.com/projects/install-on-windows/en/latest/about/releasenotes.html) and actual formal-driver verification are separate evidence.

On Windows, with sources available locally:

```powershell
.\build-modules.ps1 -Compiler PATH_TO_RTC_COMPILE_EXE -OutputDir MODULE_DIRECTORY -IsaHalf -Fast
```

`-Fast` includes experimental production and fused kernels; omit it for reference modules only. A source/code SHA256 manifest is written as `modules.json`. Build all matching modules before running a newly built host; changed kernel contracts must not be mixed with old code objects.

Linux host cross-build:

```sh
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static Development/HIP/reference_network.cpp -o reference_network.exe
```

## Run offline

```text
reference_network.exe ASSETS MODULES INPUT_RGBA_F32 NOISE_F32 OUTPUT_RGB_F32 --wmma --wave --tiled --pooled
```

Default512×512/postshift0 matches the original oracle. `--720` selects1280×768/240tokens; `--900`1600×1024/400tokens; `--1080`1920×1152/640tokens. Input/history are full processing-grid RGBA floats; output is RGB floats. Full720/1080 HIP validation remains pending.

Experimental fast900 arguments additionally use:

```text
--900 --fast-prefix --fast-deep --fast-mh --mh-wave --fused-c32 --fused-ffn --fused-mh --skip-blocks 42,43,46
```

Options: `--repeat N`, `--seed N`, `--history FILE`, `--post-shift 0..3`, `--dump EXISTING_DIR`, `--dump-only comma,separated,stages`. `--profile` collects HIP events, but negative intervals have occurred even after warmup; an invalid iteration must be discarded. Wall timing includes host work and transfers. No test figure is game FPS.

Gaussian fast math has small measured sin/cos differences; its projection is independently exact on supplied HLSL features. Each conversion site follows its actual production contract: explicit legacy half conversions oftenRTZ, matrix half casts and selected software helpersRNE. Keep the original reference path for comparisons.

## Integration and diagnostics

`device_network.cpp` checks persistent GPU-pointer inference. `bridge_network.cpp` checks shared D3D12 resources/fences without preview DirectX. The bridge requires one HIP GPU matching the D3D12 adapter and serialized calls. `Network::Enqueue` forbids host observers/readback diagnostics.

```sh
bash scripts/build-addon.sh third_party/minhook third_party/reshade/include release/HIP/dlss5-hip-candidate.addon64 --hip
```

The compile-time HIP switch preserves ordinary D3D12 codec/temporal passes and skips SDK721/experimental-SM setup. Modules default to ASSETS/HIP, overridden by `DLSS5_HIP_MODULES`. The addon defaults to the exact backend; `DLSS5_HIP_FAST=1` explicitly selects the experimental fast/fused/prepacked path. Whole-graph production parity remains outstanding.

`hlsl_network_oracle.cpp` uses Agility721 only as the production HLSL oracle. `replay_prefix.cpp` is a deliberately labelled diagnostic that injects captured block0/4 states to locate divergence; it must never be presented as normal end-to-end verification. Other validators and their ABI documents describe each independently tested family. Captures, logs, executables and code objects belong in ignored `release/HIP/`.

## 2026-09-15 weight prepacking

`--packed-weights` enables lossless initialization-time FP8 packing for MH dense matrices and, when `--fast-deep` is active, ViT FP8 linear / split projection matrices. Build with `-Fast -IsaHalf` to include the three `*-packed.hsaco` variants. Original paths remain available for A/B comparison.

Matrix bytes occupy the beginning of their original float regions. Biases/scales and region offsets stay unchanged; unused padding remains allocated in this first version. This reduces matrix reads/conversions, **not total weight allocation by four times**. FP16-only matrices keep their original representation. Non-FP8-exact coefficients are rejected rather than requantized.

`benchmark-packed-weights.ps1` runs baseline/packed/packed/baseline with a fresh process per leg, excludes the cold first iteration, checks full output SHA256 and writes timings.csv. On the900 fixture, MH-only gave no clear gain (70.413→70.222ms); adding ViT/split FP8 matrices gave70.4165→65.217ms median hot wall time, ten samples per variant. All outputs equal baseline `7b959143…`; this preserves existing output, not a new claim of matching HLSL. Seed123 with supplied history also matches baseline. Current game installs are unchanged.

## Stellar Blade trial installation (2026-09-15)

Installed DLL SHA256 `0202b4dc4ff94bb0a80300b3488b2b6e7ae942d0e4a58021c941d5924be40bba`, fast900P+packed weights, including the ReShade/native COM identity fix. Game-local DLSS5-AMD contains isolated flags/logs/23 modules and an asset junction to the validated lab asset set. Global flags, Magpie and drivers were not changed. Full temporal frame check passed at about63ms per frame; actual game validation belongs to the user trial.

After closing the game, run `D:\DLSSNR-Lab\hip-backend\stellarblade-hip\restore-stellarblade.cmd` to restore the backed-up900P HLSL DLL and disable the local HIP root. F6 only bypasses neural processing to the game's own FSR; it does not restore the old DLL.

### C32 native RTZ and diagnostics (2026-09-15)

The reference runner now accepts --wall-profile. It drains before each kernel
and measures launch through completion with a monotonic CPU clock. Reported
serialized_kernel_ms includes submission/wait overhead and changes scheduling;
it identifies candidates, not pure GPU time or normal frame percentages.
Device-only game inference rejects this diagnostic mode.

C32 fused FFN/attention defaults HIP_C32_RTZ_ISA=1, replacing software truncation
with hardware RTZ. Define 0 for the old path. test_rtz.cpp and rtz_probe.hip
validated 1,186,626 finite inputs including half boundaries. The ABBA runner
benchmark-module-swap.ps1 checks complete output hashes: seed0 65.260→61.0745ms,
seed123 65.5015→61.2275ms, identical outputs in each comparison. These are offline
wall timings. No installed module was replaced. HIP_C32_LDS_VECTOR remains an
optional disabled experiment: it showed no whole-network gain.

### Native FP8 conversion and C32 packed weights (2026-09-15)

Fast kernels default HIP_NATIVE_FP8_F=1; deep/boundary also default
HIP_NATIVE_RTZ=1. Define either as 0 for legacy conversion. The finite-domain
FP8 comparison passes 1,186,626 boundary/random inputs. Saturation and input
signed-zero normalization are explicitly preserved.

The runner supports --packed-c32 for fused FFN/attention weights; HIP_FAST now
selects it in the game adapter. A matching c32_fused_ffn_attention-packed.hsaco
is required (24 modules in a complete build). Scales/bias remain float32 at the
original offsets. Normal and packed modules must not be interchanged.

Combined offline ABBA: 61.1815→58.990ms at seed123 with equal output hashes.
The DLL compiles, but these changes have not been installed into the game.
See DevHistory for separate conversion/packing measurements and limitations.

### Byte-sized normalized QKV (2026-09-15)

--fp8-normalized requires fast MH, wave normalization and fused attention.
The producer mh_qkv_normalize_fast_wave_fp8 writes one E4M3 byte per element;
mh_attention_fused_fp8 consumes those bytes directly. Original raster
[pixel][Q,K,V][channel] indices and arithmetic are preserved. Only this tensor's
allocation is quartered; the pool's total capacity need not fall by the same
factor. Original float exports remain available.

HIP_FAST enables this path. Rebuild both multihead-fast-padded-wave-packed and
multihead_fused_attention: an older 24-module set lacks the new exports.
900 offline ABBA: 58.8955→55.3815ms with identical final RGB; explicit history
fixture: 60.177→56.7405ms, also identical. These are not game FPS measurements.

### Byte FFN hidden and attention output (2026-09-15)

--fp8-ffn selects byte expand output and byte-input contract for MH C64/128/256.
--fp8-av selects byte AV output and byte-input scalar/matrix projection for
MH C64/128/256/512. These require the compatible wave/fused pipeline; AV also
requires --fp8-normalized. HIP_FAST enables both. Rebuild the MH padded and
fused-attention modules together with the host; old exports remain available.
The byte pointers in dense kernel ABI retain pointer width but must never be
passed to float-consuming exports. Residual features and accumulators stay float.

900 ABBA combined: 55.379→51.231ms, identical RGB. FFN alone saves about3.6ms;
AV alone saves only0.14ms, not a confirmed standalone speedup. Pool ownership
remains1910.1MiB despite the smaller logical tensors. C512 split and ViT FFN
are separate kernels and are not covered by --fp8-ffn in this revision.

### Compact pipeline and optional graph replay (2026-09-15)

HIP_FAST also enables fp8_deep (split/ViT FFN hidden), fp8_middle (MH contract
output), half_c32 (already half-rounded raw output), and crop_c32 (finish plus
crop). Standalone runner flags have the same names with hyphens. These change
storage, not matrix accumulation precision. Rebuild host and the deep, MH padded,
C32 fused and boundary modules together. Complete sets still contain24 modules.
Four changes combined: normal900 ABBA51.141→47.923ms, identical RGB; real HDR
40-frame replay hot median48.476ms, final raw HDR identical to the prior HIP.

DLSS5_HIP_GRAPH=1 optionally records the warmed device network. Input/history/
output pointers or seed changes invalidate the single cache; noise updates and
host Infer also clear it. Captures cannot grow the allocation pool. External
D3D synchronization remains outside the graph. Real HDR ABBA showed under1%
benefit and periodic reset showed none, so the default remains off.
benchmark-graph-frame.ps1 checks output hashes and supports periodic resets.
API declarations follow ROCm/HIP rocm-7.1.1 hip_runtime_api.h.

benchmark_live_capture.cpp supports DLSS5_COMPARE_HLSL builds and optional
reset_every. Completion timing now submits and waits a checkpoint AFTER Frame
on the same queue. Flushing only the benchmark's earlier upload submission
missed asynchronous Frame work; earlier async CPU-only timings are invalid.
compare-frame-backends.ps1 uses matching HDR/frame conditions. Its current
HLSL async result is26.975ms, not the older fixture's16.7ms. HIP/HLSL output
parity remains unresolved; within-backend comparisons are bitwise checked.

### Fused MH QKV projection and normalization (2026-09-15)

--fused-qkv-norm requires --fp8-normalized. It retains the full FP32 projection
result in a shared64×64 tile, performs the original sequential32-channel norm,
and writes FP8 normalized output directly. Raw QKV no longer crosses global
memory on this path. HIP_FAST enables it; rebuild the MH padded module with
mh_qkv_normalize_fused and the host together. Old exports remain available.

900 ABBA47.868→45.3685ms with identical RGB. Real HDR40-frame replay hot median
45.317ms, all finite and final raw HDR identical to the earlier HIP output.
No installed game files were changed by this optimization.

### Fused multihead FFN (2026-09-15)

--fused-mh-ffn fuses expand+contract for C64/128/256. Each group handles16 tokens
with C/16 waves. Input is cooperatively quantized once, and the shared array is
reused for FP8 hidden values after a group barrier. Contract preserves the
original increasing-K order and F(Hrtz) output. Requires packed weights and
byte middle; original two-pass kernels remain available.

--tiled-mh-ffn selects [N16][K32][K][N] packed FFN weights for every channel size.
--tiled-mh-ffn-large selects them only for C256. HIP_FAST defaults to the latter:
C64/128 prefer ordinary packed rows, C256 prefers tiled weights. Third-matrix
projection weights and scales keep their original offsets/layout. New exports
have explicit c64/c128/c256 and _tiled names; rebuild host and padded MH module
together. Cooperation can be disabled at build time with HIP_FFN_COOP_INPUT=0.

Final900 ABBA45.384→43.340ms, identical RGB. Real HDR40-frame hot median43.527ms,
all finite, identical final HDR. The new DLL compiles but is not installed.
Layer comparison accepts optional fused-ffn, fused-tiled or fused-selected after
the pattern argument. Logs and intermediate variants are detailed in DevHistory.

### C32 mapped input and wave-private QKV storage (2026-09-15)

HIP_C32_LOCAL_QKV_SYNC defaults1: QKV's wave-owned16-row scratch uses memory
fences within the loop; a group barrier remains before cross-wave attention.
HIP_C32_REGISTER_FFN defaults1: retain half FFN residuals in registers and share
only packed byte operands for QKV. Define either as0 for the previous path.

--mapped-c32 reads raster input and padding directly in the fused C32 kernel,
removing the separate pack/buffer. It requires half/crop fast mode and uses a
new explicit mapped export. The preblock's already tiled input is unaffected.
HIP_FAST selects mapped input by default. Rebuild host and C32 module together.
Combined900 ABBA43.295→41.362ms, bitwise-equal RGB. Two real HDR40-frame replays
and periodic history resets also matched their previous exact output hashes.
This does not change D3D/HIP asynchronous submission settings or game installs.

### ViT16x64 output blocks (2026-09-15)

--vit-blocked makes one wave produce four adjacent16x16 expand fragments with
shared A operands; --vit-contract-blocked does the same for the K4096 contract.
Grid size is quartered. HIP_FAST enables both, retaining each fragment's K order,
the ViT activation FMA and the original serial addition of four contract parts.
Weights still use packed row layout. Rebuild host and deep module together.

--vit-split-k records an optional four-part contract plus ordered combine.
Both narrow and16x64 Split-K experiments preserved output but ran slower, so it
stays off. Final900 ABBA41.3815→39.925ms; frozen HDR40-frame hot median40.300ms,
all finite and exact final HDR unchanged. Periodic history resets also match.
No game files were deployed by these changes.

### ViT weight layout and prepacked expand input (2026-09-15)

--vit-weight-mask0..3 selects byte-tiled expand(bit0)/contract(bit1) weights;
use --vit-weight-mask 1 for the accepted variant. --vit-pack-input quantizes
expand input once into FP8 words. Explicit _tiled/_bytein exports distinguish
layout contracts. Both require the blocked byte pipeline. HIP_FAST defaults
mask1 and packed input; contract weight tiling showed no benefit and stays off.

900 ABBA40.108→39.563ms, seed/history41.3445→40.724ms, exact output preserved.
Real HDR and periodic history reset hashes also match. The latest candidate
is not installed: Stellar Blade currently uses the earlier4c0620a5 build.
The user's reported game result is900P17FPS versus earlier HLSL1080P37FPS;
these offline improvements do not establish that the practical gap is closed.

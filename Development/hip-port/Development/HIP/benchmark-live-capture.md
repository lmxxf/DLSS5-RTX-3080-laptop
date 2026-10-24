# Frozen live HDR capture probe

Build (Linux, no GPU execution):

```sh
x86_64-w64-mingw32-g++ -w -DDLSS5_USE_HIP=1 -std=c++17 -O2 -static -municode -Isrc Development/HIP/benchmark_live_capture.cpp -o /tmp/benchmark_live_capture.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

Run on the9070XT host:

```text
benchmark_live_capture.exe ASSETS FLAGS INPUT_RGBA16F OUTPUT_PREFIX [frames=30] [temporal=0|1] [HIP_MODULES]
```

Input is exactly1296×720×4 little-endian binary16 values (e.g. `live-menu-before.f16`). The source texture is `R16G16B16A16_FLOAT`; no UNORM conversion or pre-clipping occurs. Internal network900p, HIP_FAST1 (which currently selects packed production weights), persistent NativeGameFrame with its full encode/network/decode. Runtime flags are loaded only into this process; installed/game files are not changed. HIP_MODULES overrides module directory, otherwise the normal ASSETS/HIP convention applies. This HIP build has no Agility721/experimental-feature dependency.

Each frame restores the **same original HDR capture** into the target texture before processing. The previous processed output is never used as the next source. Temporal0 passes no motion and requests reset every frame. Temporal1 uses zero motion (its own correctly computed RG16_FLOAT texture footprint), resets only the first frame, and lets the ordinary Frame history path run. The same Frame instance remains alive throughout.

Outputs: `PREFIX-first.f16/.ppm`, `PREFIX.f16/.ppm`, `PREFIX.csv`. Binary16 outputs retain HDR range, tightly packed without D3D row padding. PPM is only a linear RGB0..1 clipped diagnostic preview; consult raw values for HDR. Every frame reports finite counts across RGBA, RGB min/max, luminance, dark-pixel counts, central ROI luminance/dark counts, half-value changes and maximum absolute change relative to the first processed frame. ROI is x25–75%, y20–90%; dark threshold is linear luminance0.01. CSV timing covers ProcessSubmittedFrame+completion, excluding restore/readback/statistics; this is a serialized state-reuse diagnostic, not game FPS.

Input finite/size validation runs before GPU setup. First and last frames are saved even when they are identical. Nonfinite processed output returns nonzero after statistics/output are recorded.

Optional trailing arguments (2026-09-19): after `edges_only`, `seed` defaults to 0 and `pattern` defaults to 0. Pattern 0 preserves the loaded capture; 1 replaces RGB with deterministic half-bit HDR ramps (below 8); 2 uses dark/subnormal half values. Alpha is 1 for generated patterns. These are synthetic stress inputs, not additional game captures. Existing argument lists keep their behavior.

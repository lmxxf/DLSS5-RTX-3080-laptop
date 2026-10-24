# shaders/

Two layers:

| Where | What | Status |
|---|---|---|
| `shaders/*.hlsl` (12 files) | The D3D12 glue that every current package still compiles at runtime with the system `d3dcompiler`: `native_codec_encode/decode` (input encoding, output composition, the fit/downsample path), `native_text_overlay` (status line), `native_game_rgb_input` / `native_rgb_texture` / `native_rgb_reflect` (RGB staging in and out of the network surface), `native_temporal_coordinates/feed/sample` (motion-vector handling), `native_black_probe` / `native_history_guard` / `native_output_smooth` (frame driver checks). Loaded by name from `DLSS5-AMD\native-game-tiled-assets\`. | **live** (HIP packages 0.20+, RE9 runtime) |
| `shaders/dx12-network/` (53 files) | The original Shader Model 6.10 wave-matrix implementation of the 71-block network (0.15 and earlier: C32/C64/matrix/ViT/split/post70, `native_wave_*`, `preblock_*`, the `.hlsli` helpers). Replaced by the HIP kernels in `hip/`; kept as the bit-exact reference chain and the port's history. Needs the preview DXC and developer mode described under *Historical* in the top-level README. | historical |

The HIP kernels that do the network work are in `hip/`.

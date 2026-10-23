# Deep F16 WMMA module

`deep_wmma.hip` exports the same names and argument order as the matrix subset of `deep_reference.hip`: `split_mix`, `split_expand`, `split_contract`, `split_projection`, `vit_expand`, `vit_project`, `vit_qkv_project`, `decoder_project2x`.

Use a separate module handle. Unlike the scalar module, launch block **32**, grid.x **ceil(work_items/256)**, y=z=1, shared=0. Every wave computes 16 tokens ×16 output channels, using native gfx12 F16 WMMA. Work items are unchanged from the scalar ABI (decoder uses input_tokens × output_channels). Host must require tokens%16==0 and output_channels%16==0; matrix K blocks and partitions must be divisible by32. No partial token tile, scalar GEMM fallback, or WMMA emulation is provided.

External activations/weights remain f32. Every WMMA operand must already be an exact finite binary16 value; this holds for the network's H/F lattice tensors and shipped half weights. Arbitrary f32 inputs would incur an additional operand conversion and are outside this contract. Residual f32 values follow original scalar arithmetic and half rounding. Keep the scalar module available for comparisons, not silent fallback.

Each K32 dot begins at zero and uses two K16 F16 MMAs; H(previous+dot) follows. ViT project retains four separately accumulated partitions and their half merges; QKV uses two512-channel partitions, no final F(); decoder uses four partitions only for1024 input channels. FFN activation and residual placement retain scalar boundaries. Grouped split FFN uses original eight64-channel groups and original offsets. Decoder emits clipped2×2 footprints and keeps C32 output half-valued; all other decoder outputs apply F(). All inputs must be disjoint from outputs.

Compilation: COMGR3/Clang21 gfx1201 produced191800-byte code object at `D:\DLSSNR-Lab\hip-backend\deep_wmma.hsaco`. GPU correctness/performance awaits validation; compilation is not a parity result. FP32 WMMA summation order can differ from scalar summation before H().

`deep_validate.exe ASSETS DEEP_REFERENCE_HSACO OUTPUT_PREFIX [DEEP_WMMA_HSACO]` runs the existing full ViT64 scalar D3D comparison and optionally isolated WMMA matrix comparisons. Two patterns, real block31/block23/decoder39/block66 weights. Covers decoder full2×2 footprint, cropped14×14 footprint, and C32 raw result. WMMA output sentinels detect incomplete writes; finite/bit/numeric/maxabs are reported. No fast attention substitutions are made. Failures return nonzero.

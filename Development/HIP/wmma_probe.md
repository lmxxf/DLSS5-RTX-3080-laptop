# gfx1201 FP8 WMMA probe

The device source is SDK-header-free: primitive vectors, Clang AMD builtins and function attributes only. No HIP include files or device libraries are needed. This is device code only, suitable for `hipModuleLoad` and `hipModuleGetFunction`; the host can be built with MinGW and dynamically load HIP. It does not contain `main`, hipBLAS, host templates, a scalar GEMM, or any fallback. A missing intrinsic or wrong architecture must fail compilation. Hardware validation results are recorded below.

## Verified instruction and layout

[AMD's RDNA4 example](https://gpuopen.com/learn/using_matrix_core_amd_rdna4/) establishes eight elements per lane and the gfx12 lane mapping. This probe exposes conventional row-major A/B/C buffers, loading A with row=lane%16 and B with column=lane%16. K within each instruction is `(lane/16)*8+element`; output row is `(lane/16)*8+element`. RDNA3's duplicated fragments must not be used.

[Clang 20 builtin definitions](https://github.com/llvm/llvm-project/blob/release/20.x/clang/include/clang/Basic/BuiltinsAMDGPU.def) declare `__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12` as `float8(int2,int2,float8)`. Two K16 instructions produce the requested 16×32 times 32×16 result. The K32 sparse intrinsic is not interchangeable with dense WMMA. [AMD's wide-K guide](https://gpuopen.com/learn/wmma-guide-amd-rdna-4-gpus-part-2/) also combines two instructions; its integer example's exact associativity is not proof of bit-identical floating-point sums.

## Build and launch

With a suitable HIP compiler, the intended device-only command is:

```sh
hipcc --genco --offload-arch=gfx1201 -std=c++17 -O2 -mwavefrontsize32 -fno-fast-math -ffp-contract=off wmma_probe.hip -o wmma_probe.hsaco
```

The toolchain agent must confirm this syntax for the installed compiler. If it rejects `-mwavefrontsize32`, use its documented equivalent and inspect the resulting wavefront metadata. Do not compile with fast math. Inspect disassembly for `v_wmma_f32_16x16x16_fp8_fp8`; the FP8 entry point must contain two hardware WMMA operations, and conversion must use hardware FP8 conversion. There must be no unresolved host runtime symbols in the module. Confirm device `gcnArchName` is gfx1201 before launching.

Exports `dlss5_wmma_fp8_k32` and `dlss5_wmma_f16_k32` share this ABI:

```text
(const uint8_t* A, const uint8_t* B, const float* C,
 float* D, float* after_k16, uint16_t* D_half_rne,
 uint32_t* status, uint32_t count)
```

Use grid `(count,1,1)`, block `(32,1,1)`, zero dynamic shared memory. This shape is enforced by the host; kernel indexing assumes it. All pointers are device pointers. The final count is a 32-bit value; `hipModuleLaunchKernel`'s `kernelParams` contains addresses of the pointer/scalar variables. Each independent case contains A[16][32] and B[32][16] as **raw OCP E4M3 bytes**, C/D/after_k16[16][16] as float32, D_half_rne[16][16] as raw IEEE half bits, and one status uint32. Initialize outputs and status to sentinels, synchronize before reading, require every status=0. A nonzero status or unchanged sentinel is failure. Null C is not supported; initialize a real C buffer to zeros when unused.

The separately named F16 entry decodes the same FP8 bytes to F16 and executes FP16-input/FP32-accumulator WMMA. It is a numerical comparison and never a replacement for unavailable FP8. All finite E4M3 values fit F16 exactly. Neither entry rounds the accumulator to F16 between the two K16 instructions. `after_k16` captures the first partial sum; `D_half_rne` rounds only the final FP32 result with explicit round-to-nearest-even.

Conversion export:

```text
dlss5_fp8_convert(const float* input, uint8_t* raw,
                  uint8_t* finite_sat, float* decoded, uint32_t count)
```

Launch a 1D grid with enough threads and **exactly 64 threads/block**; SDK-free conversion indexing uses that fixed block size. `finite_sat` mirrors the scalar hardware fast path in [AMD's FP8 header](https://github.com/ROCm/clr/blob/develop/hipamd/include/hip/amd_detail/amd_hip_fp8.h): clamp finite inputs to ±448, leave NaN/Inf to the conversion instruction. Return unclipped bytes alongside it. This deliberately exposes the nonfinite behavior instead of silently assuming a universal SATFINITE policy. Compare that policy with the HLSL conversion independently. Format is E4M3/OCP with bias7, max448, signed zero, minimum subnormal2^-9; it is not FNUZ/bias8/max240.

## Numerical acceptance

Keep the same binary input files on HLSL and HIP sides. Export output before activation, bias changes, normalization, FP8 repacking or downstream layers. Otherwise this is not a GEMM comparison.

1. Check all-zero, nonzero C, all-one, signed small integers, and all 32 individual K basis positions. For a basis case set A[row,k]=1 for every row and B[k,col] to distinct small signed integers; all other entries zero. This detects K order, transpose, lane16 and fragment packing errors. The small-integer results are exact in FP32 and must match every element and both K16/full-K32 outputs exactly.
2. Use fixed-seed random finite E4M3 bytes, separately restricting exponents for moderate-range tests and covering the entire finite range. Include minimum subnormal, largest subnormal, minimum normal, both zeros, ±448, mixed signs and cancellation. Form the CPU reference in float64 from decoded bytes; also record sum(abs(A*B))+abs(C) per element. Report max/mean absolute error, relative error away from zero, FP32 bit differences, signed-zero differences, and final half-bit differences. Use a conservative preliminary FP32 error bound `64*2^-24*sumabs + 2^-149`, not bit equality, for general random sums. A failing bound is a diagnostic failure, not permission to widen it until passing.
3. Compare FP8 WMMA against F16 WMMA and HLSL on identical bytes. If they differ, inspect `after_k16` first to distinguish the first instruction from the second accumulation. Exact HLSL compatibility still requires measured bit agreement for the chosen execution path; ordinary CPU tolerance is not that proof.
4. Test C near 2^24, widely separated magnitudes and heavy cancellation separately. Different reduction grouping can matter; do not infer that two K16 operations reproduce every HLSL K32 accumulator rounding decision. If HLSL uses FP16 accumulation or stores/reloads half between chunks, compare that separately, not against final-only half rounding. The GPUOpen `cvt_pkrtz` helper uses toward-zero and is deliberately not used for RNE half output here.
5. Test conversion using every finite E4M3 value, both signs of each adjacent-value midpoint and the neighboring FP32 numbers. Include 0, -0, ±2^-10, ±2^-9, ±448, ±464, ±480, finite overflow, infinities and NaNs. Require exact finite SAT bytes for the agreed HLSL policy; report nonfinite classification and raw bytes separately. NaN payload equality is not required unless the source path specifies it.
6. Save all input/output binaries and report compiler version, code-object hash, disassembly instruction, GPU/driver version and flags. No GPU success is claimed merely because the module compiles or scalar CPU reference passes.

A single wave is a correctness probe, not a throughput benchmark. Kernel launch overhead dominates this tiny workload; whole-backend performance needs a later tiled/repeated workload.

## Dynamic host validator

`wmma_validate.cpp` reuses `hip_api.h` without modifying it. Build with:

```sh
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static Development/HIP/wmma_validate.cpp -o wmma_validate.exe
```

Run `wmma_validate.exe MODULE OUTPUT_PREFIX [HIP_MAJOR=7] [DEVICE=0]`. It creates 79 cases (zero/C/ones,32 basis positions,16 random integer,24 random finite FP8,4 boundary/cancellation). It saves A/B/C, both FP8/F16 paths' full and partial FP32 output and final RNE half output, manifest and report. Finite E4M3 bytes only; NaNs are excluded from GEMM inputs. CPU reference uses double precision and a magnitude-based FP32 bound; exact small-integer cases require zero error. Each half output is independently checked against CPU RNE conversion. Exit0 means numerical checks plus FP8/F16 parity passed; exit1 means API/numerical failure; exit3 means valid numerical bounds but FP8/F16 bit differences requiring inspection. Signed-zero-only differences are counted separately. This host does not yet invoke the separate FP8 conversion kernel or prove HLSL equivalence. Parent process compiles/runs the module; this agent did not run remote GPU work.

## Hardware result (2026-09-14)

The parent process ran 79 cases on the RX9070XT. FP8 versus F16-input WMMA passed the CPU bounds and exact integer/basis checks, but differed in 2,054 partial/full FP32 values and two final half values (maximum difference4). This is recorded as an operand-instruction difference, not repaired by changing the expected arithmetic.

Direct HIP FP8 versus preview HLSL `F8_E4M3FN` then passed **all20,224 values bit-for-bit** for K32-with-initial-C, two-K16-with-initial-C, and the first K16 partial. Read-only retrieval of both sides' half files confirmed **zero half-bit differences** for those variants too: final HIP `_Float16` RNE and HLSL `Matrix.Cast<F16>` agree on these cases. For partial half, the HIP float32 partial is independently rounded using Python's IEEE half conversion because the HIP host did not save a partial-half buffer.

The deliberately different `Multiply(A,B)` followed by scalar `+C` variant differed in232 FP32 values, maximum4, while its final half results happened to agree. C placement must therefore remain explicit; half-only checking would miss this difference.

Reproduce from the saved, gitignored artifacts:

```sh
python3 Development/HIP/compare_wmma.py --root release/HIP
```

Missing binaries are errors, not skipped tests. FP32/FP16 parity is required for k32/split/partial; late-C differences are diagnostic. These measured79 cases establish the present migration baseline, not every possible FP8 matrix.

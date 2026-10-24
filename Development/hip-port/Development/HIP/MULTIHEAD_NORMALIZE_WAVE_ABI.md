# Sequential-sum wave normalization candidate

`multihead_fast_padded.hip` now appends `mh_qkv_normalize_fast_wave`. The existing scalar entry and all prior kernels remain unchanged. The new build is **`multihead-fast-padded-wave.hsaco`**, not an overwrite of either currently validated fast/padded binary.

ABI: `(const float* qkv,const float* weights,float* normalized,uint tokens,uint channels)`, identical arguments and `[pixel][Q,K,V][C]` layouts to scalar `mh_qkv_normalize_fast`. Launch block256, grid ceil(tokens×(C/32)/8). One wave handles one `(pixel,head)`, with its32 lanes handling consecutive channels. Entire out-of-range waves return uniformly.

For Q/K each lane loads one channel and squares it. The32 values are extracted with `readlane` in the exact order0,1,...,31 and added sequentially starting at0. There is no tree reduction or reassociation. The same original FP32 square sum, rsqrt floor, Q scale multiplication and final F() are preserved. V is quantized directly. Each wave performs contiguous32-float input/output accesses instead of the old one-thread-per-head strided accesses.

## Compilation inspection

SDKless COMGR3/Clang21/gfx1201 build succeeded:153,784 bytes. Remote artifact:

```text
D:\DLSSNR-Lab\hip-backend\multihead-fast-padded-wave.hsaco
```

SHA256 `3022640607f0ed3b91ee254c30adcaf355cbd8650d3907f7b59e0d9bf761acc9`. Assembly and read-only retrieved artifacts are beside it / under gitignored release/HIP.

The new entry has wave32, max block256, SGPR12, **VGPR9**, zero LDS, zero private/scratch storage. The unchanged scalar entry in the same module has SGPR12, **VGPR148**, likewise no LDS/scratch. Disassembly contains exactly64 `v_readlane_b32` instructions: two complete ascending0..31 sequences for Q and K. Register/coalescing improvements are observed compiler facts, not yet a measured speedup.

## Production and large-T host

The existing independent production-normalize host now accepts:

```text
multihead_normalize_fast_validate.exe ASSETS PRODUCTION_QKV_NORMALIZE_CSO MODULE PREFIX [C] [scalar|wave] [WIDTH] [HEIGHT] [TIMING_REPEATS]
```

Defaults preserve old behavior: C64, scalar,16×16,no timing. Select wave explicitly for candidate validation. Width/height must be positive multiples of8 and pass byte-count bounds. Actual production QKV+normalize CSO is still the oracle; the host compares its output against HIP QKV+selected normalize for both patterns and saves intermediates. The earlier CSO packing/FAST2=0 requirements still apply.

With TIMING_REPEATS>0, the host additionally benchmarks both scalar and wave normalization using the **same immutable raw-QKV buffer**, three warmups, repeated launches and HIP events. Each timed output is checked against production again. No data transfer occurs inside the event interval. Nonfinite, zero or negative event durations are labeled `event_valid=0`, reported as unavailable and discarded; CPU wall milliseconds per launch are reported separately. Invalid events do not turn into negative times or FPS. Output correctness still controls the exit code.

Choose large dimensions matching the graph stage when measuring; do not substitute M400 microbenchmarks for the complete graph. This host also runs the production QKV GEMM and writes large output files at large T, so its whole executable wall time is not normalization latency. Root schedules GPU and full-graph A/B; this authoring agent compiled and inspected only.

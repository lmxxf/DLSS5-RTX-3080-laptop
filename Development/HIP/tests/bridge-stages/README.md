# Staged bridge regression

Run from the nested project root. `prepare.py` generates `/tmp/bridge-stages/test.cpp` using current production options. Compile with MinGW C++17 -O2 -static -D_WIN32_WINNT=0x0A00, include Development/HIP and src, link d3d12/dxgi/dxguid. `run.ps1` uses the existing frozen network-timeline input/expected data and network-fixed-shapes/selected-modules, guards game processes, and checks both root/architecture and flat module layouts. Three distinct-seed frames are queued before a single wait. Failure injection replaces only the test instance's launch function pointer; it does not remove the real D3D device.

`prepare-codec.py` pins pre-change 613c278, generates old class twins and old shaders in /tmp/bridge-stages. Compile codec.cpp with -municode, include src and /tmp/bridge-stages, link d3d12/dxgi/d3dcompiler/dxguid. `run-codec.ps1` compares old/new in full1080 FP16, FIT FP16, and FIT UNORM8/sRGB. It checks legacy nondefault strengths, explicit full strengths at three paper-white scales, debug views and restoration.

`run-shaders.ps1` uses Development/tests/compile_fit_shaders.cpp (44 production variants). `compile-codec-pair.cpp` and `run-harness.ps1` additionally exercise the updated independent Development/d3d12_native_codec_test.cpp with old/new DXBC.

No game files are installed by these scripts. Test binaries and shader directories are under D:\DLSSNR-Lab\hip-backend\bridge-stages. Integration contract and TheAutomatic/PR #5 attribution: ../../staged-bridge.md.

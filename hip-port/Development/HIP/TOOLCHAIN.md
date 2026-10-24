# gfx1201 编译（2026-09-14）

无需安装 HIP SDK。amd9070 当前预览驱动提供 `C:\Windows\System32\amd_comgr_3.dll`，实测 COMGR 3.0 / 内嵌 Clang 21，支持 gfx1201。`amdhip64_6.dll` 没有 `hiprtcCreateProgram` 导出。

Linux 侧构建小型宿主工具：

```sh
x86_64-w64-mingw32-g++ -std=c++17 -O2 -static Development/HIP/rtc_compile.cpp -o /tmp/rtc_compile.exe
```

Windows 侧运行（只编译，不启动 GPU kernel）：

```text
rtc_compile.exe output.hsaco source.hip comgr
```

工具动态加载 System32 的 COMGR；`SOURCE→BC`（action 2，`-O3 -nogpuinc -nogpulib`）、`BC→RELOCATABLE`（action 4，`-O3`）、`RELOCATABLE→EXECUTABLE`（action 7，无额外选项）。同时通过 action 5 输出 `output.hsaco.s`。语言 HIP=3，ISA `amdgcn-amd-amdhsa--gfx1201`。直接 action 14 在该环境失败，三步路径通过。

`wmma_compile_probe.hip` 已产出 4,128 字节 ELF code object，汇编明确包含 `v_wmma_f32_16x16x16_fp8_fp8`，wave32，code object version 6。编译结果位于远端 `D:\DLSSNR-Lab\hip-wmma-probe.hsaco`，尚需宿主加载/执行验证。kernel 名 `wmma_probe`，参数 `(const int* packed, float* out)`，一个 32 线程 block；128 个 int32 输入全设 `0x38383838`（FP8 E4M3 的 1），256 个 float 输出应全部为 16。

这是无头文件、无设备库的内核编译路径。kernel 用 `__attribute__((global))` 声明，通过 Clang AMDGPU builtin 使用线程索引及 WMMA；尚未接入完整 HIP 标准头、设备数学库或 C++ 标准库。不要将此结果扩展成 Linux 编译 hsaco 与 Windows PAL 无条件兼容的结论。

参考源：

- COMGR API 及源码：https://github.com/ROCm/llvm-project/tree/amd-staging/amd/comgr
- 官方 HIPRTC 与 COMGR 关系：https://rocm.docs.amd.com/projects/HIP/en/docs-7.0.1/how-to/hip_rtc.html
- builtin 定义：https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Basic/BuiltinsAMDGPU.td
- Windows SDK 安装器的 GUI 可选组件，CLI 不能选择组件：https://rocm.docs.amd.com/projects/install-on-windows/en/latest/install/install.html

# 独立 AMD LLVM 构建与 HIP 模块复现

脚本在 DGX Spark 原生 aarch64 上构建 LLVM/Clang/LLD，仅启用 AMDGPU 后端。输出 AMDGPU ELF 代码对象，不需要在 Linux 上安装 ROCm SDK，也不需要 AMD GPU。Windows 游戏仍由现有 HIP 驱动加载 `.hsaco`。

## 固定源码

首轮基点：ROCm/llvm-project 的 `6d585d872fbd3c594da7a3c09ac9b22eef4167f6`，公开 `amd-staging` first-parent 路线上引入 LLVM 22 之前的最后一个 LLVM 21 提交。分支 `lmxxf/llvm-project:dlss5-gfx12`。

现役 COMGR 编译器的内部提交为 `590b9320a5be90e40268759c6203c01fde121e68`，在本地完整 amd-staging 历史中不存在。公开 ROCm 7.0.2 / 7.1.1 为 LLVM20，7.2.4 为 LLVM22，因此没有把某个 ROCm7 标签冒称为相同 LLVM21。所选基点是可复现的同主版本候选，不能证明它与内部提交的代码距离最小。版本文件与命令日志见 `Development/results/llvm-fork-20260929/`。

## 构建

在 `~/work/llvm-project` 切到上述分支后，在 297 仓运行：

```bash
bash Development/tools/llvm-fork/build.sh
```

默认输出 `~/work/llvm-build-dlss5-gfx12`，16 个编译任务、2 个链接任务。可用 `LLVM_SOURCE` / `LLVM_BUILD` / `LLVM_JOBS` 覆盖。再次运行同一脚本是增量构建；只改后端时也可直接：

```bash
cmake --build /home/lmxxf/work/llvm-build-dlss5-gfx12 -j 16 --target clang llc
```

## 模块编译

```bash
python3 Development/tools/llvm-fork/compile-modules.py --out /home/lmxxf/work/llvm-artifacts-20260929/candidate
```

直接解析 canonical `hip/build-modules.ps1` 的30行配方，不维护第二份宏清单；按相同顺序拼接 `.hip`/`.inc`。固定源文件名 `probe.hip`，CUID 按 COMGR 的长度+内容 SHA256 计算。`--generate-only` 只拼源；`--only c32-wave1` 编一个模块；`--targets gfx1201` 限定单架构。

管线复刻实际 COMGR verbose trace：HIP→优化 bitcode、bitcode→汇编及对象、LLD共享对象。前端显式 Windows x86_64 辅助 ABI、C++14、short wchar、MS兼容版本；后端 AMDHSA/gfx12，O3、无设备库。不启用 fast-math，不修改现役源码语义。每模块日志记录完整参数，manifest 记录编译器版本、源/对象哈希与耗时。

## 对比与回归

`snapshot.ps1` 只读并冻结游戏当前双架构60模块及宿主/配置哈希；已存在快照拒绝覆盖。`comgr-probe.ps1` 抓驱动编译器实际参数，不运行 GPU 核。两者经 `scp` 上传，远端使用 PowerShell `-File` 执行。

```bash
python3 Development/tools/llvm-fork/compare-kernels.py /home/lmxxf/work/llvm-artifacts-20260929/baseline /home/lmxxf/work/llvm-artifacts-20260929/candidate --out /home/lmxxf/work/llvm-artifacts-20260929/comparison
```

比较三代码/元数据段、逐核原始函数字节、静态反汇编指令数量、VGPR/SGPR/LDS/private/参数区/波宽。需要 Python msgpack。函数字节不同可能包含布局/地址变化；静态数量不代表执行路径工作量或速度。

`prepare-regression.py --out <目录>` 从已验证的 kernel-map runner 生成隔离脚本，唯一实质变化是有限输出有差异时继续其他用例，完整报告而非只看到第一例。上传生成的 `regression.ps1`、`run-regression.ps1` 与 candidate 两架构到 `D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929`；后者每阶段查空闲、校验现场未变，用同一个最新生产 host 做基线/候选 EXACT和AE七用例。不会部署候选到游戏。

最终逐位以 `results/float-fma-20260928/new-baseline-hashes.csv` 为裁判，并比较全部AE字段；编译成功不等于数值验收。gfx1200只有编译/静态对比，不能称真机通过。

## 产物管理

构建树、编译器、60模块、bitcode、对象、完整反汇编留仓外。结果目录保存精简清单、逐核CSV、日志和结论。首轮只建立管线并列优化候选，不实施编译器优化补丁。

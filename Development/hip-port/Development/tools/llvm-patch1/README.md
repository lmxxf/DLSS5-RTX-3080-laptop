# LLVM21 VOPD局部前瞻实验

源码在 `lmxxf/llvm-project` 的 `dlss5-gfx12` 分支，基点仍是公开LLVM21 `6d585d87`；只修改GCNCreateVOPD及新增两个MIR测试，不改HIP内核源码/生产配方。

开关：`-mllvm -amdgpu-dlss5-vopd-lookahead=4`，默认0。限gfx1200/1201 wave32、非strictfp。pass在寄存器分配后、memory legalizer/waitcnt/MODE/hazard/delay生成前执行；只移动同块独立纯寄存器运算，不越过内存、矩阵、MODE、同步、inline asm或bundle。RAW/WAR/WAW检查包括隐式寄存器及物理别名，移动指令清除过时kill标记。

## 构建和测试

```bash
cmake --build /home/lmxxf/work/llvm-build-dlss5-gfx12 -j 16 --target clang llc FileCheck
```

`run-lit.py --out <仓外目录>` 在轻量lit suite执行fork的两个MIR/FileCheck文件。覆盖默认关闭、目标限制、独立配对、RAW/WAR/WAW、EXEC别名、MODE/内存/同步边界、kill和距离。三个真实模块另以Clang backend `-mllvm -verify-machineinstrs` 编译BC通过。

`tools/llvm-fork/compile-modules.py` 新增可重复的 `--backend-option` 参数；默认无额外选项：

```bash
python3 Development/tools/llvm-fork/compile-modules.py --out /home/lmxxf/work/llvm-patch1-20260929/P --backend-option=-amdgpu-dlss5-vopd-lookahead=4
```

默认关集off和启用集P均完整重编60份；off对前轮公开21的.text/.rodata/.note必须60/60同。参数只传给backend两步（汇编及对象），拼接源码hash不变。通过 `tools/compiler-versions/package-version.py` 检查并打包。

## GPU门与计时

`prepare-lab.ps1` 创建隔离实验根 `D:\DLSSNR-Lab\hip-backend\llvm-patch1-20260929`，检查游戏/其他runner空闲和64项现场快照；A=驱动21、O=公开21默认关、P=开启补丁，传输后核对全部模块hash。

`prepare-runner.py --out <目录>` 从前轮已验证的gated runner生成脚本：P先过EXACT/AE七用例，再做public1/public2/driver1/driver2共四批900/1080 ABBA。每槽1000帧弃200、只读首尾；正确性12帧全部读回。不部署游戏。

传回collected-P.zip后，解压规范化Windows路径分隔符，用 `analyze.py <解压目录> --out <结果>` 独立检查golden、AE和32个计时槽。逐核比较沿用 `compare-kernels.py`，族级沿用 `family-stats.py`，所有静态数量不冒充执行周期。

8条前瞻只对C32/C64两个模块做gfx1201静态探针，未作为GPU候选，不能宣称通过数值或性能测试。编译器、模块、完整反汇编和MIR放仓外 `~/work/llvm-patch1-20260929/`。

# 编译器版本对照工具

沿用 `../llvm-fork/` 的构建、配方生成、逐核比较管线。生产HIP源码与配方不修改。

版本标签：L20 = Windows驱动COMGR2/LLVM20；A = 驱动COMGR3/LLVM21；L21 = 已验证的公开AMD LLVM21；L22 = ROCm7.2.4/LLVM22。

1. `prepare-lab.ps1` 冻结隔离目录，核对上一轮现场快照仍同。上传当前 `hip/` 源文件归档（`compiler-versions-source.zip` 放上一轮实验根），复制已有生产runner/回归脚本。
2. `build-driver.ps1` 用当前COMGR3重编60份；DGX用 `hip/compare-modules.py` 与现场快照比三段，必须全部相同，才生成 `driver-identity-pass.json`。`finalize-lab.ps1` 验哈希后把重编集作为flat-A。
3. `build-comgr2.py --out <仓外目录>` 只把rtc_compile副本的COMGR DLL选择改成2号，不改生产工具；`probe-comgr2.ps1` 查版本/目标支持，`build-comgr2.ps1` 编双架构60模块。
4. LLVM22在独立源码worktree构建：给 `../llvm-fork/build.sh` 指定 `LLVM_SOURCE`、`LLVM_BUILD`、`LLVM_JOBS`；再用 `compile-modules.py --bin <bin> --out <目录>` 编模块。ZIP只放两架构HSACO与manifest，`import-version.ps1 -Version L22` 验证传输。
5. `run-checked.ps1 -Version L20|L21|L22` 串行执行：EXACT/AE七用例→逐帧golden与全部AE字段检查→通过才做900/1080两批ABBA→收集。每槽1000帧、丢前200，性能阶段仅首尾读回；回归阶段全部读回。空闲检查包括游戏和其他lab runner；整个流程不会换游戏文件。
6. 传回collected-VERSION.zip，解压时把Windows路径分隔符规范化；`analyze-results.py` 独立核覆盖/有限值/golden/AE，并从每槽1000行CSV重新计算全部均值。不能把12帧回归中的wall_ms当性能。
7. `compare-kernels.py` 比完整模块集；`family-stats.py --comparison L20=<对比目录> ... --out <结果目录>` 依据今早900/1080两个trace选取43个活跃kernel/module对，生成逐核及族级分类。每个函数体只计一次，不加权launch/window/循环，不能当动态工作量或帧时分解。WAIT沿用已有分类（含wait/nop/delay/clause/barrier/sleep）。

全量源码/对象/HSACO/反汇编留仓外，结果目录保存manifest、CSV与原始日志压缩包。L21源码hash与上轮30个编译单元全同，编译产物复用；其刚完成的七组EXACT/AE回归经独立重验后复用，记录原始证据来源；本轮新做两批计时。驱动重编与原基线三段60/60相同。

# Phase 1：FP16 MMA / packed accumulator experiment

本实验只修改独立 CUDA 引擎；v0.1.0 的 PTX DLL 和发布包保持归档。

- `sm86_mma_prepared_core` 使用两条 `m16n8k16.f16.f16.f16.f16`，累加器为 `<4 x i32>`，顺序 `{ad01, ad23, ad45, ad67}`。
- `__sm86_c_to_ampere` 返回 `sm86_u4`；`__sm86_d_to_rdna4` 接收 `sm86_u4`。SSA pass 改写直接组合、循环 PHI、diamond PHI、LCSSA 出口并对零 C 折叠；整数返回 call 不携带浮点 `contract` flag。
- 本次保留边界的旧布局网络（8 条 scalar shfl），在其外打包/解包；尚未声称边界实现 4-shfl。K 循环中抵消成功的转换无此边界开销。A/B 准备及 FP8 解包不变。
- K32 的显式 Hrtz 与原有 FP32 partition 求和保持原语义，使用 `_f32` 布局辅助函数。没有把它们也改成 packed half add，避免一次改变两个舍入规则；核心 MMA 的累加精度已经独立改变。
- `wmma_validate_cuda MODULE --fp16-acc` 使用 63 组有限、有界输入，验证 K16/K32 两阶段、非零 C 与全部 K basis。整数案例要求精确，其余以 `4*2^-10*sumabs` 为误差界；FP8/FP16 两种输入准备路径还要求逐位一致。原 FP32 验证模式仍保留原压力案例与容差。全值域 FP8 矩阵乘可能超过 FP16 范围，不能要求该压力案例输出有限。
- `test_packed_acc_ir.py` 通过实际 `opt-14 -verify` 检查零/直接抵消与非零初值循环及出口类型。

## 复测

构建模块：`python Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip OUTPUT_DIR`。

Linux 基准：编译 `Development/HIP/benchmark_cuda_nn.cpp`（g++ C++17、O2、-ldl、-pthread），设置 `DLSS5_BENCH_SMALL_ONLY=1`，可设 `DLSS5_BENCH_DUMP=PREFIX` 保存最后一帧、`DLSS5_BENCH_PROFILE=1` 额外采集一帧核级事件与实际 launch 函数的属性（包含 compact 替换核）。参数依次为 assets、modules、warmup、iterations。

基准 1080p/900p 标签对应处理尺寸 1920×1152 / 1600×1024；报告同时比较全 padded 输出和前 1080 / 900 行可见区域。输入为基准既有的确定性 RGB 图案，Style 1、Small 31-block，无 Graph、无 adaptive reuse。PSNR 使用峰值 1.0；这是一组数值验证输入，并非真实游戏画面验收。

`analyze.py BASE_PREFIX CANDIDATE_PREFIX OUTPUT_DIR` 读取前缀对应的 `-bench.log` 和 `-WIDTH.rgb32`，生成精度、速度及逐核对照表。核级统计来自额外插桩帧，不与未插桩的端到端时间强求完全相等。OccW 是 CUDA occupancy API 的资源上限，不是实测 achieved occupancy。

## 本轮结论

见 [完整结果](results.md)：数值达到门槛，但未出现明确性能收益；1080p 21/32 核寄存器下降，pool 路径出现占用率下降与一个 104 B LMem 回退。Phase 1 的外围 packed 化/边界转换仍待完成，当前候选没有部署到稳定资产。

最终参数为 50 warmup / 80 iterations，同一 140 W 上限、默认 DVFS 未锁频。GPU/Wall 完整统计见 `f32-bench.log`、`f16-bench.log`；遥测为 `telemetry.csv`。原 `/tmp` 产物已归入本目录 `artifacts/`：`f32-source/`、`f32-modules/`、`f16-modules/`、`outputs/`、`benchmark_cuda_nn`。`validate_wmma.py` 可直接复建并运行 WMMA 探针。起始仓库版本 `11cded4e22cede2e87f5c387135637798423c004`。

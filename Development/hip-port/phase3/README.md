# Phase 3：延后解包、900p 门控、C32 寄存器 Q

三项均已实现并实测。**数值通过，但完整组合没有获得预期的净提速。当前实测更合适的子集是保留共享 Q，仅启用新的900p门控。** 所有模块和 runner 都留在实验目录，没有覆盖共享 assets、游戏或 v0.1.0 发布包。

## 构建与验证

- 新增 extern C/noinline `__sm86_unpack_fp8`；五种 WMMA wrapper 和 QKV staging 均走该入口。SSA 匹配 prep/unpack，做同基本块 CSE 与零折叠；在后置 `opt-14 -O3` 前统一 alwaysinline。
- Host 的 compact contract/projection 条件放宽为 TierGeometry/free_geometry，不再依赖 fast_numeric 或1920×1152。其他设备、功能、模块可用性限制保留。`DLSS5_LAB_COMPACT_ALL=0` 可回到原门控。
- C256 wave2 加入1600×1024/960；`DLSS5_LAB_C256_900=0` 可回到 split 路径。实际900p融合更快且输出逐位一致，因此默认启用。
- C32第一轮只计算K/V并存入两平面；Q移到消费qt循环，从residual读取同一half值、重新打包，沿用原投影/归一化顺序，最终Q直接留在寄存器。
- 最终40/40模块、1898 entry编译和CUDA加载通过；新Linux CUDA benchmark runner已重编。SSA测试通过实际LLVM verifier，GPU基础测试的置换、ones、packed add均0 bit-diff。

### 实测校准：延后解包并未解决本轮寄存器压力

独立的 deferred-only + 旧门控控制组与Phase 2整网逐位一致，但wave2仍250 regs、compact contract仍217 regs。对cubin ELF `.text.<kernel>` 的比较发现：compact contract、QKV和ViT expand的机器码段与Phase 2逐字节相同；wave2代码大小相同、字节不全同，寄存器也未降。

原始Clang IR保留noinline，后置pass已改为alwaysinline，说明入口确实生效；捕获的persistent IR里unpack call数为1154→1154，并未产生额外CSE消除。**按该内联时序的修法没有带来所预测的收益，不能把寄存器问题写成已解决。** 机器码比较不等于完整模块二进制相同，也不构成未采集的pipeline利用率证据。

## 三组最终对照（50 warmup / 80 iterations）

| 档位 | Phase 2 min / median ms | 完整Phase 3 min / median ms | 共享Q控制组合 min / median ms | 对F32可见区域PSNR |
|---|---:|---:|---:|---:|
| 900p | 41.506 / 41.929 | 41.139 / 41.879 | **40.632 / 41.009** | 46.9753 dB |
| 1080p | 53.505 / 54.067 | 54.925 / 55.420 | **53.683 / 54.370** | 46.1009 dB |

共享Q控制组合 = 延后解包 + 新门控 + 原共享Q核。它与完整Phase3模块目录**只差 `c32-wave1-fast.hsaco` 一个文件**，两个目录各40模块；此控制针对本次fast Small路径。该控制组合与完整候选两档RGB输出逐位一致。

900p/1080p均invalid=0、首末帧bit_diff=0、32/32活跃核LMem=0。可见区域maxabs为0.04004550/0.04160273。实际处理尺寸为1600×1024/1920×1152；精度亦统计完整padded区域。Style1、Small31-block、确定性合成RGB输入；不是实际游戏观感验收。

完整[32核对照表](results.md)包含新增/消失的核、Regs、LMem、SMem、OccW与分解时间；GPU总耗时不含初始化、权重打包/上传和最终读回。额外插桩帧的核累计单列，不能与未插桩整帧时间直接混算。

### 900p门控控制（20 warmup / 40 iterations，共享Q）

- compact-only：median41.230ms；再开C256 wave2：40.750ms。
- C256站累计：split FFN2.762752ms + attention1.044480ms =3.807232ms；融合3.346432ms，省0.460800ms。两个输出逐位一致，故保留。
- 新门控开启了compact W16和byte互连，`vit_pack_input`从每帧8次变为0，核种类34→32。
- 900p compact切换后的整网不与旧路径逐位一致：虽然CPU权重重排无损，选择W16 kernel也切换到了Phase2的half partition求和，并打开byte入口/出口组合。该组合对F32的PSNR通过；不能把“权重字节置换无损”扩大为整个路径天然bitwise一致。

### C32 shared memory和占用率目标实现，但没有转化为速度收益

五个主用C32核SMem10240→8192B、OccW8/9→11；prefix/post/mapped的regs分别169→146、160→152、146→152。finish/dcrop为145regs、OccW11。up仍225regs、OccW8，未越过寄存器资源门槛。

完整local-Q候选比共享Q控制在两档都更慢。新方案去掉Q共享存取，但增加了residual重读、feature重新打包和预洗牌；这些是源码可见的新增工作，不能仅凭理论OccW升高推导出延迟下降。本轮没有采集硬件pipe利用率，尚不单独量化各项新增指令的损失。

因此**8KB local-Q保留为实验候选，不推荐当作当前最快版本推广**。若只取本轮已实测的性能收益，使用 `artifacts/deferred-shared-q/` 和新Host门控；完整三项候选在 `artifacts/modules/`。

## 遥测、控制与复测

默认DVFS、未锁频、同一约140W上限，显存7001MHz。三组长负载段SM时钟中位数分别为：Phase2 1710/1740MHz、共享Q 1710/1725MHz、local-Q 1725/1710MHz（各为1080p/900p）。因此不将小差异冒充严格等频结论；完整候选没有显示预期加速这一结论也不依赖宣称固定频率。

- `results.json`：三组主数据、两个900p门控控制与精度。
- `kernel-text-comparison.json`、`deferred-ir-audit.json`：延后解包的编译证据。
- `modules.sha256.json`、`shared-q-modules.sha256.json`、`build-inputs.sha256.json`：产物与源哈希。
- `primitives.log`、`build.log`：最终验证；`build-cache-check.log`：40模块缓存复查。
- `q-reorder-first-attempt.log`与`build-first-attempt.log`等保留开发中的失败。首个Q重排版本因读入改写遗漏而错误（约36/38dB），已修复；不计入通过结果。

复测：`bash Development/hip-port/phase3/run_benchmark.sh`，可传warmup/iterations两个参数。依赖本机Phase2模块、Phase1 F32输出和本目录 `artifacts/deferred-control-source/` 冻结的控制源码。该脚本测试三组主对照；900p两个门控控制日志已单独保存。Host提供 `DLSS5_BENCH_WIDTH=1600` 供单档控制测试。

门控虽允许其他Tier/free几何及非fast_numeric，此轮只验证了本机fast Small的900p/1080p；不外推未运行配置。

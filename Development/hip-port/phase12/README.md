# Phase12：逐站 half AV/V 审计

唯一性能及输出基线是 Phase11 selected，清单见 `phase11-baseline-manifest.json`。冻结的 ptx-patcher v0.1.0、共享 assets、Windows 部署及发布包均不修改；不 push。初始工作树干净，起点 `1da7855`。

## 范围与原语证明

沿用 Small31 / Style1、Graph off、默认 DVFS、约 140 W；性能每次 50 warmup / 80 iter。每个日志自己的 GPU min/median、Wall 与独立插桩 PROFILE_TOTAL 成组报告。插桩累计不是帧均值；两者差额不能全归为 launch 气泡。时钟/功耗仅记录，未锁频，不作锁频因果判断。跨 h2 预解包和 Graph 不重试。

四个生产站分别证明，而不是外推 Phase11 Site2 的有限域结果：

| 站点 | 原生产者及零语义 | 测试的实际 FP16 MMA 次数 |
|---|---|---|
| C32 AV | FP16 RNE 累加，原始量化无额外 +0，保留 -0 | 4 |
| C32 V | FP16 RNE 累加，原始量化无额外 +0，保留 -0 | 2 |
| wave2 AV | FP16 RNE 累加，原 `w2_z0(x)=x+0`，-0→+0 | 4 |
| wave2 V | FP16 RNE 累加，原 `fmaf(x,1,+0)`，-0→+0 | C64/128/256 对应 4/8/16 |

这里没有 RTZ 生产步骤；不增加 RTZ。复用 Phase11 已证明的 half2→E4M3 RNE、subnormal、448 饱和原语。**裸 half pack 不足以证明 NaN**：负 NaN 在旧 fpext 路径的规范化与直接按原始 half 位打包不同。因此新增生产者适配器：C32 先 `mul.rn.f16x2(x,1)`，wave2 先 `add.rn.f16x2(x,+0)`，规范化 NaN 并保留各站原零语义，再调用 half pack。不能把该规则套在 float 激活多项式或 Q/K 行归一化上。

`check_producers.py` / `probe.hip` GPU 测试：每个站点、每个 32 lane×8 字节位置遍历全部 65,536 half 模式（含 ±0、subnormal、Inf、NaN 的符号/payload），另做 256 个单点布局测试；所有站点字节差异均为 0。额外用实际 `sm86_mma_prepared_core` 执行上述累加次数、随机输入及 NaN/Inf/零污染输入，也全部 0。完整比较包含 **D→RDNA4→scalar pack→preshuffle** 与 **Ampere D half pack→2-shfl AB**，不是仅比较标量编码。见 `primitive-results.json` / `primitive.log`。

## 逐站控制

实验变换在 `transform.py`，站点独立构建入口 `build_station.py SITE`。每站只替换一个模块，其余 39 个复制不可变 Phase11 baseline；构建和全部模块哈希记录在 artifacts 下。

第一轮共同基线 GPU median 32.286 ms：C32 AV 31.661、C32 V 32.066、wave2 AV 32.948、wave2 V 32.532。首轮前四项遥测未赶上采样，明确缺失；不能补造。后续所有反向/补充配对均有独立遥测。

| 站点 | 反向：候选→紧邻基线 median | 补充：基线→候选 median | 决策 |
|---|---:|---:|---|
| C32 AV | 33.884→34.013 | 32.664→32.179 | 进入最终三档复测 |
| C32 V | 33.451→33.591 | 32.451→32.413 | 补充仅 0.038 ms，证据弱，不进入默认 |
| wave2 AV | 33.323→33.328 | — | 首轮回退、反向近乎零收益，不保留 |
| wave2 V | 32.104→33.328 | — | 首轮回退、方向不稳，不保留 |

热状态/DVFS 随长轮次变化，不能把跨轮 min 拼成收益。逐次 min/median/Wall/插桩累计与遥测全部见 `results.md` / `results.json`；静态 SASS 审计见 `sass-audit.json`，指令减少不当作速度证据。最终仅 C32 AV 使用 `hip/phase12_transform.py`，挂接在 Phase11 feature pack 之后，结构匹配失败即报错；Q/K、RTZ residual、float 激活及其它站点保持原样。

## 720p F32 参考旁支

先校准参考链，再尝试 720p。归档 Phase1 Host + SHA 固定的 Phase1 F32 模块重新生成 900p/1080p，两份与既有 gold **0 bit-diff**（`f32-frozen-reproduction.json`）。当前 Host + 同一 F32 模块，显式 AMPERE_WEIGHTS=0 / COMPACT_ALL=0；1920 C256_SPLIT=0、1600/1280 C256_SPLIT=1，以旧图门控配对，900p/1080p 再次 **0 bit-diff**（`f32-current-paired-status.json`）。这两次是参考质量复现，不是 50/80 性能轮次。

然后才生成 720p，仍得到与 Phase11 被拒参考完全相同的 SHA `0c6c6b614fe43c97ebb5c228f0744d1ef9fdd05f4b7cf4b5940d6190a6684a8c`；相对 Phase11 输出的可见 PSNR 只有 **11.607545 dB**，maxabs=1。该值是**坏参考诊断**，绝非产品精度分数。门控/权重配对校准并未解决 720 路径正确性，精确根因尚未定位；需逐层对照或匹配当前图的 F32 实现。**可信 720p F32 参考仍未建立**，不报告绝对 720p PSNR，不把它阻塞相对 Phase11 的严格 0bit 主线。详情 `f32-reference-status.json`；复现 `reference_chain.py`。

## 复测入口

先构建 Host（当前源码，未修改 Host 算法）及完整默认模块，再实际 CUDA load 全入口：

```bash
c++ -O3 -std=c++17 Development/hip-port/Development/HIP/benchmark_cuda_nn.cpp -ldl -o Development/hip-port/phase12/artifacts/benchmark_cuda_nn
python3 Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip Development/hip-port/phase12/artifacts/selected/modules
python3 Development/hip-port/phase12/verify_modules.py
python3 Development/hip-port/phase12/check_producers.py
python3 -m unittest discover -s Development/hip-port/hip -p 'test_*.py'
bash Development/hip-port/phase12/run_benchmark.sh
```

`bench.py` 拒绝覆盖已有证据，复测采用新名字。共享权重只读，候选和临时文件全部落被忽略的 `artifacts/`。计时须单进程顺序运行并另启 nvidia-smi 遥测，避免其它 GPU 工作。所有三档默认开启现有 C256 wave2 门控，720p 固定 1280×768；坏 F32 参考控制的 split 设置不用于默认计时。

## 最终验收与保留结论

默认保留 **C32 AV** 一个站点；C32 V、wave2 AV/V 均不进入默认。全 half 模式/真实 MMA 原语及 16 项 Python/LLVM 回归通过。默认全量源码重编与独立 CUDA load40/40、1918entry 均通过；39模块 SHA 与 Phase11 相同，唯一变化的 c32-wave1-fast 与单站候选精确 SHA 相同。见 `selected-modules.sha256.json`、`cuda-load-verification.json`、`full-build.log`、`tests.log`、`quality.json`。

三档正反两对的完整 min/median/Wall/PROFILE_TOTAL/遥测在 [final-results.md](final-results.md)，32核分解在 [results.md](results.md)。候选两轮 GPU median：720p **14.588 / 14.884 ms**，900p **24.236 / 24.569 ms**，1080p **32.637 / 32.849 ms**；对应 Phase11 基线 **14.555 / 14.876、24.159 / 24.644、32.639 / 33.217**。所有数值按各自轮次报告，不取跨轮最好值。

1080第一对近乎持平（0.002ms），第二对正向0.368ms；追加紧邻 ABBA 两对为 **31.966→31.921、33.221→32.887ms**。此前独立站点反向和确认配对也正向，但幅度随轮次波动，只接受一个小优化，不给固定百分比。720不宣称收益，900两轮方向相反、不宣称稳定收益。插桩 PROFILE_TOTAL 也有明显运行间波动（如 ABBA-b1 33.1264ms），不将其与帧 median 的差额解释成调度气泡。

两轮三档相对 Phase11：完整处理尺寸输出0bit-diff、invalid0、首末帧一致、32/32 LOCAL0。720保持1280×768/C256 wave2，无 misaligned address。900/1080可信 F32 可见 PSNR **46.975322410562406 / 46.100947087035124dB**，maxabs **0.0400454998 / 0.0416027308**，均与基线相同；720无可信绝对PSNR。参考链 Host/module/gold SHA 在 `reference-provenance.json`，坏参考明确隔离。

SASS实查：prefix槽位12117→12035，post10252→10169；两核 `HADD2.F32` 各少32，half乘法各多16，SHFL不变。这些是编译结果的静态证据，不能单独推算动态收益。原始 PTX/SASS、实验变体及输出保留在被忽略的 artifacts；清理了本轮实验复制的39×4个不变大模块及重复中间源，输出经SHA验证后硬链接去重（`cleanup.json`），最终40模块/PTX/生成源保留。后续跑单站 benchmark 需先用 `build_station.py` 重新组成完整40模块，不能直接使用已裁剪的实验目录。

### Phase13 建议

优先解决720 F32链的逐层首次偏离：用当前Host/相同输入在stem、C32、C64/C128/C256和ViT边界输出，与可信参考实现对齐，先定位几何/图路径，不继续用坏参考计算绝对PSNR。性能侧不要盲推所有half站点；C32 V和wave2此次已经说明静态减少不保证稳定median。若继续C32，可先单独测prefix/post的动态指令与访存依赖，保留同轮整帧双向配对；不重试Graph或原样跨h2预解包。

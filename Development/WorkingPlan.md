# WorkingPlan — PTX V3.7：分支 5（680 处零常量折叠 `mov.b16 0` + 零 Spill 模块 `pack4_fb2356`）、分支 6（`FB03` 逐核剥离精选）、分支 7（`qkv_512` 单核零 Spill 剥离 `async_qkv_only`）精准攻坚（2026-11-01 02:38）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **`K-Search` 搜索纪律**：
   - `V3.6` 完成了分支 5、6、7 的首轮广度探索（当前三个分支均为 `[Open, n = 1 / 3]`），虽然 19 个粗粒度候选未直接触发三档六方向全胜，但在逐核资源表与单模块跑分中暴露出了 **3 个极其明确的局部正收益金矿**（见下方第 2 节）。
   - 本轮 `PTX V3.7` 对分支 5、6、7 发起第 2 轮精准剥离冲击（若晋升则重置对应分支 `n = 0` 并封存新 `1.00×` 基线；若未晋升则更新为 `n = 2 / 3`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 每完成一个独立子步骤，立即单独执行一次小 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V3.7` 候选构造、静态资源核验与 GPU 原语测试（`v37/*.py` + 验证 JSON）；
     - Commit 2：串行正反 ABBA 跑分汇总表与四张硬件体检表（`v37/timing-summary.md`, `v37/bench.json`, `v37/hardware-*.md`）；
     - Commit 3：更新 `v37/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 候选分支调度表（更新至 `V3.6` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 `FB01~03` 整块 `shadow` | 前四轮已满 `K=3` 剪枝 |
| **分支 5** | **`[Open]`** | **`2 / 3`** | **有界/非负生产者的 Pack 前端特化（680 处 `[0.0, 0.0]` 零常量折叠 `mov.b16 0` + 正向零 Spill 模块组合 `pack4`）** | `V3.6` 查明 680 处 `pack3` 区间恒为 `[0.0, 0.0]`（可直接折叠为 0 算术指令的常量 `0`！），且 `pack4_fb3` / `pack4_fb6` 三档均值全正，回退仅来自有 Spill 的 `FB00/01/04`；V3.7结果见文末回执 |
| **分支 6** | **`[Open]`** | **`2 / 3`** | **`FB02 / FB03` 原位 2× Shared 改写与按单入口（Entry）剥离精选** | `V3.6` 中 `fb3_selective_fast_inplace` 三档均值全正（`+0.328% / +0.012% / +0.232%`，6 向赢 5 向），需对 `FB03` 的 4 个活跃核做逐入口拆解精选；V3.7结果见文末回执 |
| **分支 7** | **`[Open]`** | **`2 / 3`** | **`FB04` 全网最重 Spill 核 `qkv_512` 单核剥离异步 Shared 耦合改写 (`async_qkv_only`)** | `V3.6` 重大发现：`async_fb4` 将 `qkv_512` 的 **`STACK` 从 `88B -> 0B`、`STL/LDL` 从 `40/29 -> 0/0`、`REG` 从 `255 -> 243`、非 NOP SASS 从 `4,515 -> 3,675`（单核净砍 `840` 条 SASS！）**，仅因捆绑了另外 3 个零 Spill 核（SASS 反增）才被拖累；V3.7结果见文末回执 |

---

## 2. 本轮派单任务（`PTX V3.7`：三大金矿精准剥离实验，由闇执行）

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v37/` 下执行以下实验：

### 任务 A（分支 7 头号金矿 `[Open ⚡, n=1/3 -> 2/3]`）：`cc_split_swin_16h_qkv_512_chained_fp8` 单核剥离与无分支向量化刷新（严格 `0 bit-diff` vs `V3.1_pack5`）
1. **为什么 `V3.6` 的 `async_fb4` 整模块微慢 `-0.35%`，但其中隐藏着全网最大的单核突破？**
   - 核查 `v36/resources.json` 发现，`async_fb4` 同时修改了 `FB04` 的 4 个核：
     - 在唯一有严重 Spill 的 **`cc_split_swin_16h_qkv_512_chained_fp8`** 上：`REG` 从 `255 → 243`，**`STACK` 从 `88 B → 0 B`（彻底清零！）**，**`STL/LDL` 从 `40/29 → 0/0`（彻底清零！）**，**`INSN_NONOP` 从 `4,515 → 3,675`（单核净减 `840` 条 SASS，`-18.6%`！）**，`PRMT` 从 `452 → 350`（净减 `102` 条）！
     - 但在另外 3 个原本就是 `0 B STACK` 的核上（`proj_pool_512` `REG 180 → 208`，`ffwd_512` `NONOP 1,951 → 2,012`，`ffwd_inpview_512` `NONOP 3,209 → 3,251`），因原本无 Spill 且 MMA 复用度低，注入协同刷新循环与额外 `bar.sync 0` 属于纯负开销！
2. **构建并测试两个精准剥离候选（其余 37 个活跃核与 `V3.1_pack5` 100% 相同）**：
   - **候选 `v37_async_qkv_only`**：仅对 `FB04` 的 `cc_split_swin_16h_qkv_512_chained_fp8` 单个入口启用 `V3.6` 的 `async_shared` 改写，其余 `FB04` 入口保持 `V3.1_pack5` 原代码不变！
   - **候选 `v37_async_qkv_unrolled`**：在 `v37_async_qkv_only` 基础上，针对 `qkv_512` 固定 `128` 线程（`ntid = 128`）刷新固定大小 Shared 符号的事实，将 `refresh_code` 中每次 `4B` 的带分支 `while` 循环（`setp.ge + @done bra + ld.shared.u32 + st.shared.v2.u32 + add + bra`）改为 **无分支展开的直接偏移加载/解码/写出（或 `v2.u32 / v4.u32` 向量化读写，省去循环比较跳转与 `%ntid` 动态乘法）**！

### 任务 B（分支 5 金矿 `[Open ⚡, n=1/3 -> 2/3]`）：680 处 `[0.0, 0.0]` 零常量直接折叠 `mov.b16 0` + 零 Spill 正向模块 `pack4` 组合
1. **候选 `v37_pack_zero_const`（严格 `0 bit-diff` vs `V3.1_pack5`）**：
   - `v36/pack-range-audit.json` 已严格证明：全网被归为 `pack3` 的 **680 处** `cvt.rn.satfinite.e4m3x2.f16x2 %rs_dst, %r_src;`，其源寄存器 `%r_src` 的静态区间 **100% 恒为 `[0.0, 0.0]`（正零常量）**！
   - 在 `V3.6` 的 `pack_proven` 中，这 680 处仍发射了 `pack3` 的 3 条算术指令（`HMUL2 + LEA + PRMT`）；请将其直接替换为编译期常量赋值 **`mov.b16 {dest}, 0;`**（**0 条算术指令**，且当一对零常量被后续 `mov.b32 %r_pack, {%rs_lo, %rs_hi}` 拼接时，编译器可直接折叠为硬件零寄存器 `RZ`）！
2. **候选 `v37_pack4_clean`（零 Spill 正向模块组合：`v37_pack_zero_const` + 仅在 `FB02, FB03, FB05, FB06` 开启 `pack4`）**：
   - `V3.6` 逐模块测试表明，`pack4` 在有 Spill 的 `FB00` (`STL/LDL 107/108 -> 110/111`, 900p `-0.994%`)、`FB01` (1080p `-0.145%`) 和 `FB04` (900p `-0.241%`) 上回退，而在零 Spill 的 `FB02`、`FB03`（三档全正）、`FB05`、`FB06`（三档全非负）上保持零 Spill 且三档输出相对 `V3.1_pack5` 实测 `0 bit-diff`。请测试 `pack4_fb2356` 与 `pack4_fb36`（叠加 680 处零常量折叠）。

### 任务 C（分支 6 金矿 `[Open ⚡, n=1/3 -> 2/3]`）：`FB03` 四入口逐核剥离精选与跨分支强强联合
1. **`V3.6` 中 `fb3_selective_fast_inplace` 三档均值全正（`+0.328% / +0.012% / +0.232%`，6 个方向赢 5 个）**：
   - `FB03 (C256)` 共有 4 个活跃入口：`inpview_tilesync`、`ds_wait`、`outview_wait`、`upsample_tilesync`。
   - 请核查这 4 个入口在 `fb3_selective_fast_inplace` 下的各自 `REG / INSN_NONOP / PRMT` 变化，测试在 `FB03` 内部排除 `REG` 增长最多或收益最弱的入口后的子集候选（如仅 `inpview + outview + ds_wait` 或仅 `REG` 下降核），以及与任务 A (`v37_async_qkv_unrolled`)、任务 B (`v37_pack_zero_const`) 的联合候选！

---

## 3. 验收、分支表结算与小颗粒度 Git 提交纪律
1. 所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档全胜及预设质量门，立即封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v37.dll` 并升格为新 `1.00×` 基线（重置对应分支 `n = 0`）；若未通过，则将对应分支计数从 `n = 1 / 3` 更新为 `n = 2 / 3`。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

### V3.7 执行回执（2026-11-01）

本轮无晋升，保持V3.1_pack5为唯一1.00×。 分支5 Open n=2/3；分支6 Open n=2/3；分支7 Open n=2/3。所有首轮六方向全胜候选已repeat，计数{'smoke': 42, 'timed': 312, 'repeat': 24}。完整[回执](ptx-patcher/v37/README.md)、[正反配对](ptx-patcher/v37/timing-summary.md)、[验收与清理](ptx-patcher/v37/validation.json)。九个保护路径不变，三小提交，不加Co-Authored-By，不push；保留剩余Open分支，未以本轮结果宣布全局收敛。

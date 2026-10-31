# WorkingPlan — PTX V3.6：顺着《0105 审核意见》第 4 节三大性能缺口立项新分支 5、6、7 攻坚（2026-11-01 01:25）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **顺着审稿缺口深挖，绝不靠免责措辞早停**：
   - 闇在 [《性能评估20261101-0105》审核意见](doc/性能评估20261101-0105-审核意见.md) 中给出了“不认可按‘可兑现性能上限已证明’正式停工”的裁决，并在第 4 节明确指出了 **3 个在声明边界内尚未被构造性实测排除的具体技术方向**。
   - 按照 Zero 的迭代铁律（“如果闇不认可，就继续从闇的反馈中寻找性能缺口、寻找优化点”），主脑已修正 `0105` 报告中的 5 处硬账（commit `7dbe484`），并将闇第 4 节指出的 3 个未排除方向正式增列为 `K-Search` 候选分支调度表的 **分支 5、分支 6、分支 7**，立即启动 **`PTX V3.6`** 实测！
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 每完成一个独立子步骤，立即单独执行一次小 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：分支 5（Pack 源范围证明与 `pack4 / pack3` 前端特化）与分支 6/7（`FB02/03` 原位及按核精选、`FB04/05` Shared/Async 耦合）的分析、构建与 GPU 原语验证（`v36/*.py` + 验证 JSON）；
     - Commit 2：串行正反 ABBA 跑分汇总表与四张硬件体检表（`v36/timing-summary.md`, `v36/bench.json`, `v36/hardware-*.md`）；
     - Commit 3：更新 `v36/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与扩展后的 `K-Search` 候选分支调度表（7 分支体系）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1** | `[Pruned]` | `3 / 3` | `.maxnreg` 跨硬件驻留台阶（`FB00/01/04/05`） | `V2.8` 及 `V3.2` 6 核 cap 控制均未过全档全胜，已剪枝 |
| **分支 2** | `[Pruned]` | `3 / 3` | 通用 `FP16 -> FP8` 打包与双对 `Quad` 融合 | `V3.3` `quad_all/fb23` 与 `V3.4` `quad_fb1/local` 均未过两轮全胜，已剪枝 |
| **分支 3** | `[Pruned]` | `3 / 3` | 非直通 (`non-mapped`) FP8 解码临时池、重排、重算与等价算术 | `V3.0`、`V3.2`、`V3.3` 共 18 个候选均未过两轮全胜，已剪枝 |
| **分支 4** | `[Pruned]` | `3 / 3` | 原表示 CFG 转发拓宽与 `FB01~03` 整模块 `shadow` / `FB01 inplace` | `V3.3~V3.5` 已完成 144 项（含 36 项子集）CFG 反证与 7 个整模块候选实测，已剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`0 / 3`** | **有界/非负生产者的 Pack 前端特化（`Range-Proven Pack4 / Pack3`，省去 `HMNMX2 448` 甚至 `LOP3`）** | **源自《0105 审核意见》§4.3**：若源寄存器在前序指令中已明确饱和（`<=448`）或非负有界（`[0, 448]`），可省去前端 `min.f16x2 448`（`abs` 折叠进 `HMUL2 |R|, 2^-8` 成 **4-SASS Pack**）或再省去符号 `LOP3`（成 **3-SASS Pack**） |
| **分支 6** | **`[Open ⚡]`** | **`0 / 3`** | **`FB02 / FB03` 原位（`In-Place`）2× Shared 改写与按入口/按段零 Spill 精选** | **源自《0105 审核意见》§3.4 & §4.2**：`V3.5` 的 `shadow` 保留原 1× store 使镜像写流量变为 3×，且 `FB02/03` 未测 `inplace`，`fb3_exact_shadow` 在 720p/1080p 已呈正向；需测试 `FB02/03 inplace` 及按单核/单段（零新增 Spill）精选 |
| **分支 7** | **`[Open ⚡]`** | **`0 / 3`** | **`FB04 / FB05` Shared 阶段与 `cp.async` 异步耦合表示改写** | **源自《0105 审核意见》§4.1**：`V3.5` 仅测了 `FB01~03`，主动排除了 `FB04/05`；需审计 `FB04/05` 全部 Shared 阶段（区分纯本地量化段与 `cp.async` 段）并构造可装入原槽位的耦合改写候选 |

---

## 2. 本轮派单任务（`PTX V3.6`：三箭齐发攻克分支 5、6、7，由闇执行）

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v36/` 下执行以下三项构造性实验：

### 任务 A（分支 5 `[Open ⚡]`）：全网 8,944 处 Pack 源寄存器数据流范围审计与 `pack4 / pack3` 前端特化
1. **静态 CFG 数据流范围与符号审计（输出 `v36/pack-range-audit.json`）**：
   - 对 `FB00..FB06` 全部 8,944 处 `cvt.rn.satfinite.e4m3x2.f16x2` 的源寄存器 `%src`，沿 CFG 向上追溯其定义指令链（如 `min.f16x2`、`max.f16x2`、带 `.sat` 修饰符的半精度指令、常量、或特定已知有界算子）：
     - 统计有多少处 `%src` 在静态数据流上**已保证有界 `|x| <= 448.0` 且非 NaN**（即前端 `min.f16x2 v31_a, v31_a, 0x5f005f00` 纯属冗余夹断）；
     - 统计有多少处 `%src` 在静态数据流上**已保证非负有界 `0.0 <= x <= 448.0`（且 `+0.0`）**（即不仅 `abs` 与 `min 448` 冗余，连恢复符号位的 `lop3 0xd8` 也冗余）。
2. **构建并验证 `pack4`（4 核心 SASS）与 `pack3`（3 核心 SASS）原语及整网候选**：
   - **`pack4`（针对有界 `|x| <= 448` 源，4 条核心 SASS）**：
     ```ptx
     abs.f16x2 v36_a, {source};
     mov.b32 v36_t, 0x1c001c00;
     mul.rn.f16x2 v36_a, v36_a, v36_t;   // ptxas -O4 将 abs 100% 折叠进 HMUL2 R, |src|, 2^-8！
     shl.b32 v36_a, v36_a, 1;
     add.u32 v36_a, v36_a, 0x007f007f;   // LEA
     lop3.b32 v36_a, {source}, v36_a, 0x7f007f00, 0xd8; // LOP3
     prmt.b32 v36_a, v36_a, 0, 0x4431;   // PRMT
     cvt.u16.u32 {destination}, v36_a;
     ```
   - **`pack3`（针对非负有界 `0 <= x <= 448` 源，3 条核心 SASS）**：
     ```ptx
     mov.b32 v36_t, 0x1c001c00;
     mul.rn.f16x2 v36_a, {source}, v36_t; // HMUL2
     shl.b32 v36_a, v36_a, 1;
     add.u32 v36_a, v36_a, 0x007f007f;   // LEA (因 |x|<=448，乘 2^-8 后 bit 14..15 恒为 0，+0x7f 不会溢出至 bit 15)
     prmt.b32 v36_a, v36_a, 0, 0x4431;   // PRMT
     cvt.u16.u32 {destination}, v36_a;
     ```
   - 用独立 `ptxas -O4` 验证 `pack4`（4 条核心 SASS：`HMUL2 |R| -> LEA -> LOP3 -> PRMT`）与 `pack3`（3 条核心 SASS：`HMUL2 -> LEA -> PRMT`）的机器码及 33,554,432 对有界域 GPU 原语 `0 mismatch`。
   - **构建两类整网候选**：
     1. **`v36_pack_proven`（严格 `0 bit-diff` vs `V3.1_pack5`）**：仅对静态 CFG 已证明有界/非负的位点应用 `pack4 / pack3`；
     2. **`v36_pack4_ empirical`（实证有界探索，须过 `nonfinite == 0`、`PSNR >= 50 dB`、`maxabs <= 1/64`、天空 `变号 == 0` 质量门）**：探测在 `FB00..FB06` 中哪些模块/核的实际运行时激活值从不超出 `[-448, +448]`（即应用 `pack4` 后在三档测试帧上仍然保持 `0 bit-diff` 或满足严格质量门且 `nonfinite = 0`），并测试其三档正反 ABBA 速度！

### 任务 B（分支 6 `[Open ⚡]`）：`FB02 / FB03` 原位（`In-Place`）2× Shared 改写与按入口/按段零 Spill 精选
1. **消除 `shadow` 的 3× 写冗余，构建 `FB02 / FB03` 原位 `inplace` 候选**：
   - 在 `V3.5` 中，`FB02` 与 `FB03` 仅测试了保留原 1× store 的 `shadow`（写流量 3×）；请对 `FB02 / FB03` 中写端全部来自有限 `pack5` 的 Shared 阶段（或非 pack 写入段在写端同步解包为 `f16x2`）实施 **原位 2× 替换（删除原 1× FP8 `st.shared`）**。
2. **按入口与按阶段零 Spill 精选（`v36_shm_selective`）**：
   - 针对 `V3.5` 中 `fb2_exact_shadow` 新增 `69/55 STL/LDL` 而 `fb3_exact_shadow` 保持 `0/0 STL/LDL` 且在 720p (`+0.136%`)、1080p (`+0.027%`) 正向的事实，按单核（Entry）与单 Shared 交换阶段（Epoch）筛选出 **编译后 `STACK` 与 `STL/LDL` 均不增加且 `CTA/SM` 驻留不变** 的子集构建精选候选（含精确 `exact` 与近似 `fast`），执行三档正反 ABBA 实测。

### 任务 C（分支 7 `[Open ⚡]`）：`FB04 / FB05` Shared 阶段与 `cp.async` 异步耦合表示审计与改写实测
1. **逐段审计 `FB04 (C512)` 与 `FB05 (ViT)` 的全部 Shared 符号与读写阶段（输出 `v36/fb45-shared-audit.json`）**：
   - 对 `FB04`（352 个 `shared_load` 解码事件）与 `FB05`（256 个 `shared_load` 解码事件）中的每一个 Shared 数组与每一个 barrier 周期（Epoch），明确区分：
     - **类型 I（纯核内 `st.shared` 生产段）**：该阶段无 `cp.async` 写入，写端 100% 为核内寄存器 `st.shared`；
     - **类型 II（`cp.async` 硬件异步拷贝生产段）**：该阶段由 `cp.async.cg.shared.global`（16B 密排 FP8）直接从全局显存搬入 Shared Memory。
2. **构造并实测 `FB04 / FB05` 耦合改写候选**：
   - 对 **类型 I** 阶段（或通过独立 Shared 缓冲区与 `cp.async` 解耦后仍保持官方 API 当前 `CTA/SM` 驻留且能装入原 PE 槽位的 `FB04/05` 核），实施 Shared 2× FP16 耦合改写（精确版与近似 `fast` 版）；
   - 对 **类型 II**（`cp.async` 16B FP8 硬件直传段），定量审计若在 `cp.async` 到达后增加协同解包再写回 Shared 所需的额外 `LDS + 算术 + STS + BAR` 指令数，并实测或给出构造性验证，完成分支 7 的实验闭环。

---

## 3. 验收、分支表结算与小颗粒度 Git 提交纪律
1. 所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档全胜及预设质量门，立即封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v36.dll` 并升格为新 `1.00×` 基线（重置对应分支 `n = 0`）；若未通过，则如实更新分支 5、6、7 的计数与状态。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

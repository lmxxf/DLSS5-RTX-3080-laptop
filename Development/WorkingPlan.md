# WorkingPlan — PTX V4.0：站在 `PTX V3.8` 基线上发起分支 5 第 2 轮冲击（`n = 1/3 -> 2/3`：零 Spill 模块 `UP-Pair` 剥离、跨块 CFG `UP-Pair` 拓宽与 `Pack4` 联合）（2026-11-01 04:06）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **`K-Search` 分支状态**：
   - 当前唯一 `1.00×` 对比基线为 **`PTX V3.8` (`zero_const_fb456`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`（SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`）。
   - 分支 1~4、分支 6、分支 7 共 6 个分支均已 `[Pruned, 3 / 3]`；仅剩 **分支 5 `[Open ⚡, n = 1 / 3]`**（`V3.9` 中 `v38_pack4_fb2356` 首轮六向全胜、`repeat` 三档均值全正但 720p/900p 反向微负；`up_pair_all` 与 `up_pair_clean` 使 38 活跃核非 NOP SASS 从 `150,672` 暴降至 `148,109 / 148,449` 且 `STL/LDL` 降至 `99/100`）。
   - 本轮 `PTX V4.0` 对分支 5 发起第 2 轮精准剥离与 CFG 拓宽冲击（若晋升则重置 `n = 0` 并升格新 `1.00×` 基线；若未晋升则更新为 `n = 2 / 3`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V4.0` 候选构造、跨块 CFG `UP-Pair` 证明与 GPU 原语测试（`v40/*.py` + 验证 JSON）；
     - Commit 2：相对 `V3.8` 基线的串行正反 ABBA 跑分汇总与四张硬件体检表（`v40/timing-summary.md`, `v40/bench.json`, `v40/hardware-*.md`）；
     - Commit 3：更新 `v40/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V3.9` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.8` (`zero_const_fb456`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4, 6, 7** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 Shared 2× 耦合 / Async 协同 | 前六分支已满 `K=3` 剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`1 / 3`** | **有界/常量生产者的转换特化与 32 位直解 `UP-Pair`（零 Spill 核剥离、跨块 CFG `UP-Pair` 拓宽与 `Pack4` 联合）** | `V3.9` 中 `up_pair_clean` 净砍 `2,223` 条 SASS（`150,672 -> 148,449`）且 `STL/LDL` 降至 `99/100`，900p/1080p 四向全胜（1080p `11.009 ms`）；`v38_pack4_fb2356` 首轮六向全胜、`repeat` 三档均值全正 |

---

## 2. 本轮派单任务（`PTX V4.0`：分支 5 第 2 轮冲击 `n = 1/3 -> 2/3`，由闇执行）

请严格以 **`PTX V3.8`**（SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v40/` 下执行以下实验：

### 任务 A：剥离有 Spill 核（`FB00/FB01`）的零 Spill `UP-Pair` 候选（严格 `0 bit-diff` vs `V3.8`）
- `V3.9` 资源表揭示：`up_pair_clean` 同时修改了有静态 Spill 的 `FB00`（`outview_wait 16B STACK`、`ds_wait 8B STACK`、`inpview 8B STACK`）与 `FB01`（`ds_wait 64B STACK`、`inpview 64B->56B STACK`），以及完全零 Spill 的 **`FB02`（4 核净减 `641` 条 SASS）、`FB03`（4 核净减 `651` 条 SASS）、`FB04`（5 核净减 `104` 条 SASS）、`FB05`（3 核净减 `61` 条 SASS）**。
- 在 `V3.9` 实测中，`up_pair_all` 在 720p (`+0.334%`) 和 900p (`+0.450%`) 四向全胜，而 `up_pair_clean` 在 900p (`+0.588%`) 和 1080p (`+0.409%`) 四向全胜、仅在 720p 受 `FB00/01` 排程影响微退 `-0.123%`。
- 请构建并测试两个精准隔离的严格 `0 bit-diff` 候选：
  1. **`v40_up_pair_fb2345`**：仅在 **100% 零 Spill 的 `FB02 + FB03 + FB04 + FB05`** 上启用同基本块 `UP-Pair`（保持 `FB00, FB01, FB06` 与 `V3.8` 逐字节一致，净减 `1,457` 条 SASS 且完全不触碰任何 Spill 核）；
  2. **`v40_up_pair_fb1inp_2345`**：在 `v40_up_pair_fb2345` 基础上，仅额外纳入 `FB01` 中唯一使 `STACK` 从 `64 B → 56 B`（`STL/LDL` 从 `11/15 → 10/14`）下降的单核 `cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8`！

### 任务 B：跨基本块（`Cross-Block`）1,031 对 `UP-Pair` 的 CFG 可达定义与路径无覆写证明（严格 `0 bit-diff` vs `V3.8`）
- `v39/up-pair-summary.json` 显示：全网 2,372 对（4,744 处）`mov.b32 {%rs_lo, %rs_hi}, %r_src32` + `cvt` 中，有 1,341 对（2,682 处）位于同一基本块，另有 **1,031 对（2,062 处）属于 `cross_block`**。
- 请用 CFG 可达定义分析检查这 2,062 处 `cross_block` 独立 `UP` 转换（输出 `v40/cross-block-up-audit.json`）：
  - 若到达某条 `cvt.rn.f16x2.e4m3x2 %r_dst, %rs_half;` 的 `%rs_half` 在 CFG 上具有**唯一可达定义** `def_idx: mov.b32 {%rs_lo, %rs_hi}, %r_src32;`（无守卫），且在从 `def_idx` 到该 `cvt` 的**所有 CFG 可达路径上 `%r_src32` 均未被重新定义（Unclobbered along all CFG paths）**，则同样可以 100% 等价地直接从 `%r_src32` 用 `0x9180 / 0xb3a2` 解包（当一对 `%rs_lo, %rs_hi` 的所有消费者均被替换且无其他读取时，删除原 `mov.b32` 拆分）！
  - 构建并测试跨块拓宽后的 **`v40_up_pair_cfg_clean`**（仅在 `REG / STACK / STL / LDL` 不增加且 `CTA/SM` 不降的入口启用）。

### 任务 C：`UP-Pair` 零 Spill 子集与 `v38_pack4_fb2356` 联合候选
- 在 `V3.9` 中，`v38_pack4_fb2356` 是唯一首轮三档六方向全胜（`+0.212% / +0.543% / +0.258%`）且 `repeat` 三档均值全正（`+0.101% / +0.003% / +0.113%`）的候选；
- 请构建并测试 **`v40_joint_up_fb2345_pack4_fb2356`**（将任务 A 的 `v40_up_pair_fb2345` 与 `v38_pack4_fb2356` 结合）及 **`v40_joint_up_cfg_pack4_fb2356`**！

---

## 3. 验收、分支结算与小颗粒度 Git 提交纪律
1. 所有候选以 **`PTX V3.8`**（SHA256 `da27f34c...`）为唯一 `1.00×` 对照基线，所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll` 并升格为新 `1.00×` 基线（重置分支 5 `n = 0`）；若未通过，则将分支 5 计数从 `n = 1 / 3` 更新为 `n = 2 / 3`。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

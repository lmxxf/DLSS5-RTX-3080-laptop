# WorkingPlan — PTX V4.2：站在 `PTX V4.0` 基线上发起分支 5 第 2 轮冲击（`n = 1/3 -> 2/3`：`FB00` 排除 `pre_block` 的 `Pack4`、`FB01` 降 Spill `Pack4` 与 7-SASS `Pack4_Quad`）（2026-11-01 04:53）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **`K-Search` 分支状态**：
   - 当前唯一 `1.00×` 对比基线为 **`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`（SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）。
   - 分支 1~4、6、7 均已 `[Pruned, 3 / 3]`；`V4.1` 完成了分支 5 在 `V4.0` 基线上的第 1 轮增量尝试（分支 5 更新为 **`[Open ⚡, n = 1 / 3]`**）。
   - 本轮 `PTX V4.2` 对分支 5 发起第 2 轮冲击（若晋升则重置 `n = 0` 并升格新 `1.00×` 基线；若未晋升则更新为 `n = 2 / 3`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V4.2` 候选构造、`pack4_quad` 7-SASS 原语测试与静态资源核验（`v42/*.py` + 验证 JSON）；
     - Commit 2：相对 `V4.0` 基线的串行正反 ABBA 跑分汇总与四张硬件体检表（`v42/timing-summary.md`, `v42/bench.json`, `v42/hardware-*.md`）；
     - Commit 3：更新 `v42/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V4.1` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`
  - 38 个活跃 FP8 核静态账本：`INSN_NONOP = 145,461`，`HMMA = 13,188`，`PRMT = 18,781`，`STL/LDL = 99/100`。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4, 6, 7** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 Shared 2× 耦合 / Async 协同 | 前六分支已满 `K=3` 剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`1 / 3`** | **有界/常量生产者的转换特化（`FB00` 排除 `pre_block` Spill 核的 `Pack4`、`FB01` 降 Spill `Pack4` 与 7-SASS `Pack4_Quad`）** | `V4.1` 完成了 `FB04 pool / FB06 UP` 与 `FB02/03` 零折叠 (`n=1`)；本轮针对 `FB00 pre_block` 单核 Spill 隔离、`FB01` 降 Spill 与 7-SASS `pack4_quad` 发起第 2 轮冲击 (`n=1->2`) |

---

## 2. 本轮派单任务（`PTX V4.2`：分支 5 第 2 轮冲击 `n = 1/3 -> 2/3`，由闇执行）

请严格以 **`PTX V4.0`**（SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v42/` 下执行以下实验：

### 任务 5.1：`FB00` 排除 `pre_block` 后的零新增 Spill `Pack4`（`v42_pack4_fb0_nopre`）
- 核查 `v36/resources.json` 发现，此前 `pack4_fb0` 在 `V3.6` 中之所以使全网 `STL/LDL` 从 `107/108` 升至 `110/111` 并在 900p 暴慢 `-0.994%`，**唯一罪魁祸首是 `FB00` 的 `cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8`（全网最大 Grid 核，1080p 达 `34,560 CTA`）在 `pack4` 下 `STACK` 从 `0 B → 16 B`（新增 `3/3 STL/LDL`）**！
- 而在 `FB00` 的其余 5 个活跃核（`upsample_tilesync`, `outview_wait`, `ds_wait`, `inpview_tilesync`, `post_block`）上，`REG`、`STACK` 与 `STL/LDL` 100% 不增加，且非 NOP SASS 净减 `160` 条。
- 请在 `V4.0` 基线上构建并测试 **`v42_pack4_fb0_nopre`**（对 `FB00` 排除 `pre_block` 后的 5 个活跃核启用 `pack4`，严格要求 `FB00` 各核 `STACK / STL / LDL` 不高于 `V4.0` 基线）。

### 任务 5.2：`FB01` 降 Spill 核的 `Pack4`（`v42_pack4_fb1_clean`）
- 核查 `v36/resources.json` 发现，`pack4` 在 `FB01 (C64)` 上使 `upsample` 的 `STL/LDL` 从 `15/19 → 14/17`，使 `ds_wait` 的 `STACK` 从 `64 B → 56 B`（`STL/LDL` 从 `11/15 → 10/14`），使 `inpview` 的 `STACK` 从 `64 B → 56 B`（`STL/LDL` 从 `11/15 → 10/14`），合共削减 `474` 条 SASS 与 `3/4` 条 Spill。
- 请在已开启 `UP-Pair` 的 `V4.0` 基线上构建 `FB01` 的 `pack4`，核查在 `V4.0` 上 `FB01` 4 个活跃核的 `STACK / STL / LDL` 变化，并测试仅保留 `STACK / STL / LDL` 不增核的 **`v42_pack4_fb1_clean`**。

### 任务 5.3：7-SASS `Pack4_Quad` 双对融合（`v42_pack4_quad_fb23` 与 `v42_pack4_quad_clean`）
- 此前 `V3.1 / V3.3 / V3.4` 测试的 `Quad` 均为基于 5-SASS `pack5` 的 9-SASS `pack5_quad`；而在 `V4.0` 中，`FB02` 与 `FB03` 已默认使用 4-SASS `pack4`。
- 当把两条相邻的 `pack4` 与 `mov.b32 %dst, {%lo, %hi}` 融合为 **`pack4_quad`** 时，省去两条独立的 `prmt 0x4431` + `cvt.u16.u32` 并由末尾单条 `prmt.b32 %dst, vq_lo, vq_hi, 0x7531;` 一步拼出 32 位结果，**核心 SASS 从两次独立 `pack4` + 拼接的 9 条降至 7 条（`2 × HMUL2 |R| + 2 × LEA + 2 × LOP3 + 1 × PRMT`，平均每对仅 3.5 条 SASS，在 `FB02+FB03` 活跃核上直接再砍 `848` 条 `PRMT`）**！
- 请用独立 `ptxas -O4` 验证 `pack4_quad` 的 7 条核心 SASS 与 33,554,432 对 GPU 原语 `0 mismatch`（相对两次独立 `pack4`），并在 `V4.0` 基线上测试 **`v42_pack4_quad_fb23`**（在 `FB02 + FB03` 启用 `pack4_quad`）及其无 Spill 增长子集 **`v42_pack4_quad_clean`**，以及与任务 5.1/5.2 的优选联合候选！

---

## 3. 验收、分支结算与小颗粒度 Git 提交纪律
1. 所有候选以 **`PTX V4.0`**（SHA256 `749daadb...`）为唯一 `1.00×` 对照基线，所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v42.dll` 并升格为新 `1.00×` 基线（重置分支 5 `n = 0`）；若未通过，则将分支 5 计数从 `n = 1 / 3` 更新为 `n = 2 / 3`。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

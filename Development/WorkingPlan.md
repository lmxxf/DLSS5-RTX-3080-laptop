# WorkingPlan — PTX V4.3：分支 5 第 3 次终极冲击（`n = 2/3 -> 3/3`：剔除 `FB00` 的 `FB01 Pack4 + FB02/03 7-SASS Quad` 强强联合与 `FB01 Pack4_Quad`）及 7 分支全表终极结算（2026-11-01 05:20）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **`K-Search` 7 分支终极闭环纪律**：
   - 当前唯一 `1.00×` 对比基线为 **`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`（SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）。
   - 分支 1~4、6、7 共 6 个分支均已 `[Pruned, 3 / 3]`；仅剩的 **分支 5** 在 `V4.0` 基线上已完成 `V4.1`（`n = 1/3`）与 `V4.2`（`n = 2/3`）两轮测试。
   - 本轮 `PTX V4.3` 对分支 5 发起 **第 3 次（最后一次 `n = 2/3 -> 3/3`）终极冲击**：
     - 若有候选通过首轮 + `repeat` 两轮三档六方向全胜及预设质量门，则封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v43.dll` 并重置 `n = 0`；
     - 若本轮候选仍未通过两轮三档六方向全胜门槛，则 **分支 5 正式达到 `n = 3 / 3` 并结算为 `[Pruned, 3/3]`，全表 7 大分支 100% 闭环（`Open = 0`）**！
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V4.3` 候选构造与静态资源/质量核验（`v43/*.py` + 验证 JSON）；
     - Commit 2：相对 `V4.0` 基线的串行正反 ABBA 跑分汇总与四张硬件体检表（`v43/timing-summary.md`, `v43/bench.json`, `v43/hardware-*.md`）；
     - Commit 3：更新 `v43/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成 7 分支终极结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V4.2` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`
  - 38 个活跃 FP8 核静态账本：`INSN_NONOP = 145,461`，`HMMA = 13,188`，`PRMT = 18,781`，`STL/LDL = 99/100`。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4, 6, 7** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 Shared 2× 耦合 / Async 协同 | 前六分支已满 `K=3` 剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`2 / 3`** | **有界/常量生产者的转换特化（剔除 `FB00` 负向因子的 `FB01 Pack4 + FB02/03 7-SASS Pack4_Quad` 组合与 `FB01 Pack4_Quad`）** | `V4.2` 中 `pack4_fb1_clean` (`+0.262/+0.105/+0.039%`) 与 `pack4_quad_clean` (`+0.351/+0.174/+0.077%`) 三档均值全正，而 `joint_A_B_pack4_quad_clean` 因捆绑了 1080p 两向全负的 `A (pack4_fb0_nopre)` 在 900p 反向微差 `-0.097%`；本轮执行第 3 次终极冲击 (`n=2->3`) |

---

## 2. 本轮派单任务（`PTX V4.3`：分支 5 第 3 次终极冲击 `n = 2/3 -> 3/3`，由闇执行）

请严格以 **`PTX V4.0`**（SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v43/` 下执行以下终极实验：

### 任务 5.1：剔除 `FB00` 负向因子的 `B + Quad_clean` 强强联合（`v43_fb1_pack4_fb23_quad`）
- 在 `V4.2` 中：
  - `fixed_A` (`pack4_fb0_nopre`) 在 1080p 正反两向均为负（`-0.118% / -0.173%`）；
  - 而 `fixed_B` (`pack4_fb1_clean`：使 `FB01` 非 NOP SASS 净减 `488` 条、全网 `STL/LDL` 从 `99/100` 压降至 **`98/98`**) 与 `pack4_quad_clean`（在 `FB02+03` 的 8 个零 Spill 活跃核上融合 424 组 7-SASS `pack4_quad`，净减 `842` 条非 NOP SASS 与 `847` 条 `PRMT`）各自三档均值全部为正，且 `joint_A_B_pack4_quad_clean` 在 6 个方向中赢了 5 个（720p `+0.221%/+0.204%`、1080p `+0.145%/+0.404%`、900p 正向 `+0.834%`，仅 900p 反向 `-0.097%`）！
- 请构建并测试完全不碰 `FB00`（`FB00` 保持 `V4.0` 原 cubin 逐字节不变）的 **`v43_fb1_pack4_fb23_quad`**（即仅组合 `pack4_fb1_clean` + `pack4_quad_clean`，38 活跃核非 NOP SASS 从 `145,461` 降至 **`144,131`**，净减 `1,330` 条 SASS，`PRMT` 净减 `847` 条，`STL/LDL` 降至 `98/98`）！

### 任务 5.2：`FB01` 降 Spill 三入口精选 + `FB02/03 Pack4_Quad`（`v43_fb1_spill3_fb23_quad`）
- 在 `FB01` 的 4 个活跃入口中，`upsample`、`ds_wait`、`inpview` 三个入口在 `pack4` 下 `STL/LDL` 实质下降（从 `99/100 → 98/98`），而 `outview_wait` 保持 `104 B STACK (23/23 STL/LDL)` 不变。请构建并测试仅在 `FB01` 的这 3 个降 Spill 入口开启 `pack4` 并叠加 `FB02/03 pack4_quad_clean` 的 **`v43_fb1_spill3_fb23_quad`**。

### 任务 5.3：`FB01 + FB02 + FB03` 全部无 Spill 增长核启用 7-SASS `Pack4_Quad`（`v43_fb123_pack4_quad_clean`）
- 在 `FB01` 启用 `pack4` 后，其内部的 `164` 对活跃 `Quad` 同样可融合为 7-SASS `pack4_quad`。请先查询 `FB01` 启用 `pack4_quad` 后的逐入口 `REG / STACK / STL / LDL`，筛选出 `STACK / STL / LDL` 不高于 `V4.0` 且 `CTA/SM` 不降的 `FB01` 入口与 `FB02/03 pack4_quad_clean` 组成 **`v43_fb123_pack4_quad_clean`** 进行实测。

---

## 3. 验收、7 分支全表终极结算与小颗粒度 Git 提交纪律
1. 所有候选以 **`PTX V4.0`**（SHA256 `749daadb...`）为唯一 `1.00×` 对照基线，所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. **7 分支全表终极结算**：
   - 若有任何候选通过首轮 + `repeat` 两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v43.dll` 并升格为新 `1.00×` 基线（重置分支 5 `n = 0`）；
   - 若本轮候选仍未通过两轮三档六方向全胜门槛，则 **分支 5 正式达到 `n = 3 / 3` 并结算为 `[Pruned, 3/3]`**！至此，包含《0105 审核意见》第 4 节全部新增方向在内的 **7 大预设候选分支全部完成 `K = 3` 闭环（全表 `Open = 0`）**！
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

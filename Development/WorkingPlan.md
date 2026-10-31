# WorkingPlan — PTX V4.1：站在新晋升 `1.00×` 基线 `PTX V4.0`（1080p `<11.00 ms`，`145,461` SASS）上继续深挖分支 5（驻留不变 `UP-Pair` 补全、80 处 `FB02/03` 正零折叠与 `FB04` 零 Spill `Pack4`）（2026-11-01 04:30）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **连续两代阶梯晋升（`V3.1_pack5 → V3.8 → V4.0`）**：
   - 在 `PTX V4.0` 中，候选 `joint_up_cfg_pack4_fb2356`（全路径无覆写证明解锁跨块 `UP-Pair` 共直解 1,288 处 UP / 删除 644 个半字拆分 + `FB04/05/06` 500 处正零折叠 + `FB02/03/05/06` `pack4`）相对 `V3.8` 取得 **首轮（`+0.826% / +1.422% / +0.610%`）与 `repeat`（`+0.497% / +0.827% / +0.658%`）两轮 12/12 正反方向全胜**（1080p 压入 **`10.987 ~ 10.995 ms`** 首次击穿 11ms 大关，38 核非 NOP SASS 从 `150,672` 暴降至 **`145,461`**，27 次输出检查相对 `V3.8` 全为 `0 bit-diff`）！
   - 从本轮 `PTX V4.1` 起，**`PTX V4.0` (`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`) 正式成为唯一 `1.00×` 对比基线**；分支 5 连续未晋升计数再次重置为 **`[Open ⚡, n = 0 / 3]`**（分支 1~4、6、7 保持 `[Pruned, 3 / 3]`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V4.1` 候选构造与静态资源/原语验证（`v41/*.py` + 验证 JSON）；
     - Commit 2：相对新基线 `V4.0` 的串行正反 ABBA 跑分汇总与四张硬件体检表（`v41/timing-summary.md`, `v41/bench.json`, `v41/hardware-*.md`）；
     - Commit 3：更新 `v41/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V4.0` 晋升后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`
  - 38 个活跃 FP8 核静态账本：`INSN_NONOP = 145,461`（相比 `V3.1_pack5` 的 `152,076` 累计净减 `6,615` 条，相比 `V3.8` 的 `150,672` 净减 `5,211` 条），`HMMA = 13,188`，`PRMT = 18,781`，`STL/LDL = 99/100`。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4, 6, 7** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 Shared 2× 耦合 / Async 协同 | 前六分支已满 `K=3` 剪枝 |
| **分支 5** | **`[Open]`** | **`1 / 3`** | **有界/常量生产者的转换特化与 32 位直解 `UP-Pair`（在 `V4.0` 基线上补全驻留不变零 Spill 核 `UP-Pair`、`FB02/03` 80 处正零折叠与 `FB04` 零 Spill 核 `Pack4`）** | `V3.8` 与 `V4.0` 连续两代两轮 12/12 全胜晋升并重置 `n=0`；当前唯一 `[Open]` 分支；V4.1结果见文末 |

---

## 2. 本轮派单任务（`PTX V4.1`：在 `V4.0` 新基线上深挖分支 5 剩余增量，由闇执行）

请严格以新晋升的 **`PTX V4.0`**（`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v41/` 下执行以下实验：

### 任务 5.1：纳入 `FB04 proj_pool_512` 与 `FB06 dec_input_upsample` 两个零 Spill 且官方驻留不变核的全路径 `UP-Pair`（严格 `0 bit-diff` vs `V4.0`）
- 核查 `v40/resources.json` 与 `v40/select_clean.py` 发现：`V4.0` 的 `up_pair_cfg_clean` 机械排除了 `q['REG'] > b['REG']` 的两个零 Spill 核：
  1. **`FB04 cc_split_swin_16h_proj_pool_512_chained_fp8`**：`REG` 从 `180 → 181`（128 线程核，官方 Occupancy API 返回的 **`resident_CTA_per_SM = 2` 完全不变**，`STACK = 0 B, STL/LDL = 0/0` 不变），而单核非 NOP SASS 从 `6,001 → 5,841`（**净减 `160` 条 SASS，`PRMT` 净减 `32` 条**）！
  2. **`FB06 cc_dec_input_upsample_1024_512_tilesync_fp8`**：`REG` 从 `203 → 206`（64 线程核，官方 Occupancy API 返回的 **`resident_CTA_per_SM = 4` 完全不变**，`STACK = 0 B, STL/LDL = 0/0` 不变），而单核非 NOP SASS 从 `3,855 → 3,533`（**净减 `322` 条 SASS，`PRMT` 净减 `64` 条**）！
- 请在 `V4.0` 基线上构建并测试：
  - **`v41_up_occ_keep`**（将筛选准则从 `REG nonincrease` 修正为 **`STACK/STL/LDL nonincrease and resident_CTA_per_SM nondecrease`**，即在 `V4.0` 上纳入上述 `FB04 proj_pool_512` 与 `FB06 dec_input_upsample` 两个核的 `UP-Pair`，使 38 活跃核非 NOP SASS 从 `145,461` 进一步降至 **`144,979`**，跌破 `14.5` 万条大关）；
  - 以及单模块增量的 **`v41_up_add_fb6`**（仅在 `V4.0` 上补入 `FB06` `-322` 条 SASS）与 **`v41_up_add_fb4pool`**（仅在 `V4.0` 上补入 `FB04 proj_pool_512` `-160` 条 SASS）。

### 任务 5.2：在 `V4.0` 基线上叠加 `FB02 + FB03` 的 80 处正零常量折叠（严格 `0 bit-diff` vs `V4.0`）
- `V4.0` 目前仅折叠了 `FB04/05/06` 的 500 处正零转换；而在 `FB02 (40 处)` 与 `FB03 (40 处)` 中，正零折叠 `mov.b16 dst, 0` 在 `V4.0` 已开启 `UP-Pair + Pack4` 的模块上可进一步消除 `80` 处冗余转换且不触碰 `FB00/01`。请构建并测试 **`v41_zero_fb23456`**（在 `V4.0` 上增加 `FB02+FB03` 的 80 处正零折叠）。

### 任务 5.3：在 `V4.0` 基线上扩展 `FB04` 零 Spill 核（或 `FB00/01` 零 Spill 核）的 `Pack4`
- `V4.0` 的 `pack4` 目前覆盖 `FB02, FB03, FB05, FB06`；在 `FB04` 的 9 个活跃核中，除 `qkv_512` 外其余 8 个核均为 `0 B STACK`。请构建并测试 **`v41_pack4_add_fb4_nospill`**（在 `V4.0` 基础上对 `FB04` 的 8 个零 Spill 活跃核启用 `pack4`），以及任务 5.1 + 5.2 + 5.3 的优选联合候选！

---

## 3. 验收、分支结算与小颗粒度 Git 提交纪律
1. 所有候选以 **`PTX V4.0`**（SHA256 `749daadb...`）为唯一 `1.00×` 对照基线，所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v41.dll` 并升格为新 `1.00×` 基线（重置分支 5 `n = 0`）；若未通过，则将分支 5 计数更新为 `n = 1 / 3`。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

### V4.1 执行回执（2026-11-01）

本轮无晋升，保留V4.0为唯一1.00×。 分支5 Open 1/3，其他六分支保持Pruned3/3，Open=1。实际完整配方新增UP的FB06为203→206 REG、3855→3533 SASS，保持0 Spill/4 CTA，pool保持0 Spill/2 CTA，两核合计总SASS144979；已按实际数据修正原计划。联合选择`joint_up_add_fb4pool_zero_pack4`，所有首轮六向全胜均repeat，计数{'smoke': 27, 'timed': 144}。[完整回执](ptx-patcher/v41/README.md)、[配对结果](ptx-patcher/v41/timing-summary.md)、[验收清理](ptx-patcher/v41/validation.json)。十一保护路径不变，无.log碎文件，临时大二进制清理，三个小提交，无Co-Authored-By、不push。

# WorkingPlan — PTX V3.8：分支 5、6、7 第 3 次终极冲击（`n = 2/3 -> 3/3`）与 7 分支全表闭环结算（2026-11-01 03:12）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **`K-Search` 7 分支终极闭环纪律**：
   - 前四分支（分支 1~4）已满 `K = 3` 剪枝；根据《0105 审核意见》第 4 节新增的 **分支 5、分支 6、分支 7** 已完成 `V3.6`（`n = 1/3`）与 `V3.7`（`n = 2/3`）两轮实测。
   - 本轮 `PTX V3.8` 针对 `V3.7` 逐核跑分筛出的最后一批正向子集发起 **第 3 次终极冲击（`n = 2/3 -> 3/3`）**：
     - 若有候选通过首轮 + `repeat` 三档六方向全胜及预设质量门，则封存晋升为 `v38.dll` 并重置对应分支 `n = 0`；
     - 若本轮候选仍未通过两轮三档六方向全胜门槛，则 **分支 5、分支 6、分支 7 全部达到 `n = 3 / 3` 并正式结算为 `[Pruned, 3/3]`（全表 7 大分支 `Open = 0`）**！
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V3.8` 候选构造与验证脚本（`v38/*.py` + 验证 JSON）；
     - Commit 2：串行正反 ABBA 跑分汇总与四张硬件体检表（`v38/timing-summary.md`, `v38/bench.json`, `v38/hardware-*.md`）；
     - Commit 3：更新 `v38/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成 7 分支终极结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V3.7` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 `FB01~03` 整块 `shadow` | 前四轮已满 `K=3` 剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`2 / 3`** | **有界/非负生产者的 Pack 前端特化（零常量折叠 `mov.b16 0` 无 `REG` 增长精选 + 纯 `pack4_fb36`）** | `V3.7` 中 `pack4_clean36` 首轮六向全胜，`repeat` 720p (`+0.410%`)/1080p (`+0.332%`) 全赢，仅 900p 回退 `-0.417%`（因全网 `pack_zero_const` 使 `FB00 upsample REG 205->208`）；本轮执行第 3 次冲击 (`n=2->3`) |
| **分支 6** | **`[Open ⚡]`** | **`2 / 3`** | **`FB03` 原位 2× Shared 改写正向双入口（`inpview + upsample`）精选** | `V3.7` 逐核测试查明 `FB03` 中 `ds_wait` (`-0.416%`) 与 `outview` (`-0.897%`) 为负向源，而 `inpview` (`+0.026/+0.824/+0.111%`) 与 `upsample` (`+0.039/+0.441/+0.124%`) 三档均值全正；本轮执行第 3 次冲击 (`n=2->3`) |
| **分支 7** | **`[Open ⚡]`** | **`2 / 3`** | **`FB04/05` Shared 与 `cp.async` 异步耦合表示（`proj_pool_512` 单核剥离与 `FB04` 零折叠联合）** | `V3.6` 整模块 `async_fb4/5/45` 与 `V3.7` 单核 `async_qkv_only/unrolled` 均已验证；本轮测试剩余唯一 SASS 下降核 `proj_pool_512` 单核剥离及 `FB04 qkv` 零常量 `STL/LDL 40/29->33/22` 路径 (`n=2->3`) |

---

## 2. 本轮派单任务（`PTX V3.8`：分支 5、6、7 第 3 次终极冲击 `n = 2/3 -> 3/3`，由闇执行）

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v38/` 下执行以下终极闭环实验：

### 任务 A（分支 5 终极冲击 `[Open ⚡, n=2/3 -> 3/3]`）：排除 `FB00/01` 干扰的零常量折叠与纯 `pack4_fb36`
1. **`v38_zero_const_fb26`（严格 `0 bit-diff` vs `V3.1_pack5`）**：
   - `v37/resources.json` 显示，全网 680 处 `mov.b16 dst, 0` 零常量折叠在 `FB00` 上使 `upsample_tilesync` 的 `REG` 从 `205 → 208`，而在 **`FB02..FB06`** 上不增加任何核的 `STACK`，且使 **`FB04 qkv_512` 的 `STL/LDL` 从 `40/29` 降至 `33/22`、`FB05 expand_chained` `REG` 从 `180 → 178`、`FB06` `REG` 从 `214 → 198`**！
   - 请构建仅在 `FB02..FB06`（或仅在 `FB04+FB05+FB06` `v38_zero_const_fb456`）启用零常量折叠的严格 `0 bit-diff` 候选。
2. **`v38_pack4_pure36` 与 `v38_pack4_fb26_clean`**：
   - `V3.7` 的 `pack4_clean36` 捆绑了全网 `FB00..06` 的 `pack_zero_const`；请测试 **纯 `FB03 + FB06` `pack4`（不改 `FB00..02, FB04..05` cubin）**，以及 **`v38_zero_const_fb26` + `FB03/06 pack4`**。

### 任务 B（分支 6 终极冲击 `[Open ⚡, n=2/3 -> 3/3]`）：`FB03` 正向双核 `inpview + upsample` 原位耦合精选
- `V3.7` 对 `FB03` 四个入口的单核消融已经定位清楚：`ds_wait`（720p `-0.416%`）与 `outview`（720p `-0.897%`）是拖累 `FB03` 的负向源，而 **`inpview_tilesync`（`+0.026% / +0.824% / +0.111%`）与 `upsample_tilesync`（`+0.039% / +0.441% / +0.124%`）三档均值全部为正**，且 `V3.7` 的 `regdown` (`ds_wait+upsample`) 和 `noinp` (`ds_wait+outview+upsample`) 恰好漏掉了 **`inpview + upsample`** 这一组合！
- 请构建并测试 **`v38_fb3_inp_up_fast`**（仅对 `FB03` 的 `inpview_tilesync` 与 `upsample_tilesync` 开启原位 fast 耦合）与对应的精确版 **`v38_fb3_inp_up_exact`**（严格 `0 bit-diff`）。

### 任务 C（分支 7 终极冲击 `[Open ⚡, n=2/3 -> 3/3]`）：`FB04 proj_pool_512` 单核异步耦合剥离与联合验证
- 在 `FB04` 的 4 个 eligible 异步耦合核中，`V3.7` 单独测试了 `qkv_512`；请补齐测试另一个静态非 NOP SASS 下降且 `PRMT` 从 `488 → 368`（净减 `120` 条）的单核 **`cc_split_swin_16h_proj_pool_512_chained_fp8` (`v38_async_pool_only`)**，以及与任务 A/B 最佳候选的联合版本。

---

## 3. 验收、7 分支全表终极结算与小颗粒度 Git 提交纪律
1. 所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. **7 分支全表终极结算**：
   - 若有任何候选通过两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll` 并重置对应分支 `n = 0`；
   - 若本轮全部候选均未通过两轮三档六方向全胜门槛，则 **分支 5、分支 6、分支 7 全部正式达到 `n = 3 / 3` 并结算为 `[Pruned, 3/3]`**！至此，包含《0105 审核意见》第 4 节全部三个新增方向在内的 **7 大候选分支全部达到 `[Pruned, 3/3]`（剩余 `Open = 0`）**！
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

# WorkingPlan — PTX V3.9：站在新晋升 `1.00×` 基线 `PTX V3.8` 上深挖分支 5（无 `REG` 增长零常量扩展、`V3.8 + pack4_fb36` 与 2,372 对 32 位直解 `UP-Pair`）（2026-11-01 03:40）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程

1. **阶梯封存升格 `1.00×` 基线（`ForgeKernel` 规程）**：
   - 在 `PTX V3.8` 中，精确候选 `zero_const_fb456`（对 `FB04/05/06` 的 500 处正零转换直接赋 `mov.b16 dst, 0`）通过首轮（`+0.238% / +0.653% / +0.133%`）与 `repeat`（**`+0.357% / +0.623% / +0.264%`**）两轮 12/12 正反方向全胜且 100% 严格 `0 bit-diff`，已正式封存为 **`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`（SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`）**。
   - 从本轮 `PTX V3.9` 起，**`PTX V3.8` (`nvngx_dlssnr_sm86_v38.dll`) 正式成为唯一 `1.00×` 对比基线**（清零 `V3.1_pack5` 的历史功劳）；同时分支 6、分支 7 已在 `V3.8` 满 `K = 3` 正式剪枝（`[Pruned, 3/3]`），分支 5 因晋升重置为 **`[Open ⚡, n = 0 / 3]`**（全表 7 大分支仅剩分支 5 为 `Open = 1`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - **严禁生成/提交任何单次运行 `.log` 碎文件**（进程输出直接内嵌于 `bench.json` / `repeat.json`）！
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`V3.9` 候选构造、静态资源核验与 GPU 原语测试（`v39/*.py` + 验证 JSON）；
     - Commit 2：相对新基线 `V3.8` 的串行正反 ABBA 跑分汇总与四张硬件体检表（`v39/timing-summary.md`, `v39/bench.json`, `v39/hardware-*.md`）；
     - Commit 3：更新 `v39/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成本轮分支结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 7 分支调度表（更新至 `V3.8` 晋升后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.8` (`zero_const_fb456`)**，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`
  - 38 个活跃 FP8 核静态账本：`INSN_NONOP = 150,672`（相比 `V3.1_pack5` 的 `152,076` 净减 `1,404` 条），`HMMA = 13,188`，`PRMT = 19,549`（净减 `312` 条），`STL/LDL = 100/101`（`FB04 qkv_512` 从 `40/29` 降至 `33/22`）。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史/审稿依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1~4** | `[Pruned]` | `3 / 3` | 驻留跨阶 / 通用 Pack&Quad / 解码临时池 / 原表示转发与 `FB01~03` 整块 `shadow` | 前四轮已满 `K=3` 剪枝 |
| **分支 5** | **`[Open ⚡]`** | **`0 / 3`** *(V3.8 晋升重置)* | **有界/常量生产者的转换特化（剩余 180 处无 `REG` 增长正零折叠、`V3.8 + pack4_fb36`、以及 2,372 对 32 位免拆半字 `UP-Pair` 直解）** | `V3.8` (`zero_const_fb456`) 两轮 12/12 全胜晋升并重置 `n=0`；当前唯一 `[Open]` 分支，继续在 `V3.8` 新基线上深挖 |
| **分支 6** | `[Pruned]` | `3 / 3` | `FB02 / FB03` 原位 2× Shared 改写与按入口/按段零 Spill 精选 | `V3.6 ~ V3.8` 三轮测完原位、单入口与 `inpview+upsample` 双入口均未晋升，已满 `K=3` 剪枝 |
| **分支 7** | `[Pruned]` | `3 / 3` | `FB04 / FB05` Shared 阶段与 `cp.async` 异步耦合表示改写 | `V3.6 ~ V3.8` 三轮测完 `async_fb4/5/45`、`qkv_only/unrolled`、`pool_only` 均未晋升，已满 `K=3` 剪枝 |

---

## 2. 本轮派单任务（`PTX V3.9`：在 `V3.8` 新基线上深挖分支 5，由闇执行）

请严格以新晋升的 **`PTX V3.8`**（`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`，SHA256 `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v39/` 下执行以下实验：

### 任务 5.1：剩余 180 处正零常量转换的无 `REG` 增长精选扩展（严格 `0 bit-diff` vs `V3.8`）
- `V3.8` 折叠了 `FB04 (176) + FB05 (288) + FB06 (36) = 500` 处正零转换；剩余 `180` 处位于 `FB00 (36)`、`FB01 (64)`、`FB02 (40)`、`FB03 (40)`。
- 核查 `v37/resources.json` 可知，全网 680 处零折叠之所以在 `V3.7` 中使 `FB00` 出现 `REG` 增长，**唯一原因是 `FB00` 的 `cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8` 单核 `REG` 从 `205 → 208`**；而在 `FB00` 其余核、`FB01`（64 处，削减 126 条 SASS）、`FB03`（40 处，削减 86 条 SASS）上，`REG` 与 `STACK` 完全不增加！
- 请在 `V3.8` (`fb456`) 基线上测试：
  1. **`v39_zero_fb1456`**：`FB01 + FB04 + FB05 + FB06`（`564` 处正零折叠）；
  2. **`v39_zero_fb3456`**：`FB03 + FB04 + FB05 + FB06`（`540` 处正零折叠）；
  3. **`v39_zero_no_fb0up`**：全网 `680` 处正零折叠中仅排除 `FB00 upsample_tilesync` 单个入口（`664` 处正零折叠，38 活跃核无任何核 `REG` 或 `STACK` 上升！）。

### 任务 5.2：在 `V3.8` 新基线上叠加正向模块 `pack4`（`v39_pack4_fb36` 与 `v39_pack4_fb2356`）
- 在 `V3.7` 中，`pack4_clean36` 首轮六方向全胜（`+0.644% / +0.487% / +0.354%`）、`repeat` 720p (`+0.410%`) 与 1080p (`+0.332%`) 全胜，当时仅因绑定了全网 `FB00..06` 零折叠而在 900p 回退；而在 `V3.8` 中我们只测了不含 `fb456` 零折叠的 `pack4_pure36`，尚未测试 **`V3.8` (`zero_const_fb456`) + `FB03/06 pack4` (`v39_v38_pack4_fb36`)** 以及 **`V3.8` + `FB02/03/05/06 pack4` (`v39_v38_pack4_fb2356`)**！请在本轮补齐这两个相对于 `V3.8` 的直接增量候选。

### 任务 5.3：全网 4,744 处独立 `cvt.rn.f16x2.e4m3x2` 的 32 位免拆半字直解 `UP-Pair`（严格 `0 bit-diff` vs `V3.8`）
- 静态审计发现：全网 `FB00..FB06` 的 **4,744 处**独立 `cvt.rn.f16x2.e4m3x2 %r_dst, %rs_src;`，其 16 位源寄存器 `%rs_src` **100%（4,744 / 4,744）定义自 32 位拆半字指令 `mov.b32 {%rs_lo, %rs_hi}, %r_src32;`（共 2,372 对）**！
- 在 `V3.1_pack5` 和 `V3.8` 中，每对仍先通过 `mov.b32 {%rs_lo, %rs_hi}, %r_src32;` 拆成两个 `.b16` 寄存器（含高半字右移），再分别跑两次 7 指令 `fast_fp8_pair_to_half_lines`（`prmt 0x1404 + and + and + shr + or + mov + mul`）。
- 请实现 **32 位源寄存器直解 `UP-Pair`**：
  - 当 `%rs_src` 来自同一基本块无守卫 `mov.b32 {%rs_lo, %rs_hi}, %r_src32;`（且 `%r_src32` 在 `mov` 与 `cvt` 之间未被覆写）：
    - 若 `%rs_src == %rs_lo`（低 16 位）：直接对 32 位 `%r_src32` 执行 `prmt.b32 %r_dst, %r_src32, %r_src32, 0x9180; and.b32 %r_dst, %r_dst, 0x017f017f; shl.b32 %r_dst, %r_dst, 7; mov.b32 dlssnr_fp8_scale, 0x5c005c00; mul.rn.f16x2 %r_dst, %r_dst, dlssnr_fp8_scale;`；
    - 若 `%rs_src == %rs_hi`（高 16 位）：直接对 32 位 `%r_src32` 执行 **`prmt.b32 %r_dst, %r_src32, %r_src32, 0xb3a2;`**（直接从 32 位寄存器的 byte 2, 3 解包，彻底省去 `%rs_hi` 的半字拆分！）+ `and 0x017f017f + shl 7 + mul 0x5c005c00`；
    - 当 `%rs_lo` 与 `%rs_hi` 在后续无其他读取时，删除 `mov.b32 {%rs_lo, %rs_hi}, %r_src32;`。
  - 在 `V3.8` 基线上测试全网 `v39_up_pair_all` 以及仅在 `REG/STACK` 不增加的模块/核上开启的精选版本 `v39_up_pair_clean`！

---

## 3. 验收、分支结算与小颗粒度 Git 提交纪律
1. 所有候选以 **`PTX V3.8`**（SHA256 `da27f34c...`）为唯一 `1.00×` 对照基线，所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 若有任何候选通过两轮三档六方向全胜及预设质量门，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v39.dll` 并升格为新 `1.00×` 基线（重置分支 5 `n = 0`）；若未通过，则将分支 5 计数更新为 `n = 1 / 3`。
3. **严格执行 3 个干净的小颗粒度 Git Commit（不留任何单次 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

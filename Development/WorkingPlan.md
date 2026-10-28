# WorkingPlan — 审核《性能评估20261028-0335.md》与 PTX V2.8 Per-Kernel 精准驻留跃迁攻坚（2026-10-28 03:35）

## 0. 当前基线
- 唯一基线：**`PTX V2.7`**（commit `0329743`，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v27.dll`，SHA256 `28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969`）
  - 同轮配对 `V2.6` 实测（50 warmup / 80 iter，正反 ABBA/BAAB）：720p `6.079 → 6.022 ms`（`-0.938%`）、900p `8.839 → 8.780 ms`（`-0.670%`）、1080p `11.617 → 11.504 ms`（`-0.975%`），170 次运行末帧全部相对 `V2.6` 严格 `0 bit-diff`。

---

## 1. 任务一：严格审核 `Development/doc/性能评估20261028-0335.md`
主脑已完全吸收上一轮 `0207` 审核意见，撰写了 [性能评估20261028-0335.md](doc/性能评估20261028-0335.md)。请继续以最严苛标准审核该报告：
1. 核对一、二节所有数字、口径是否与 `v27` 证据 100% 吻合；
2. 审查第三节提出的 **`FB05` / `FB04` / `FB00` Per-Kernel 独立 `.maxnreg` 跃迁靶点** 是否存在任何被忽视的限制（如动态 Shared Memory、编译器 spill 陡增、或 Grid 波次整除关系），输出 `Development/doc/性能评估20261028-0335-审核意见.md`（及对应核验 JSON）。

---

## 2. 任务二：执行 `PTX V2.8` Per-Kernel 精准 `.maxnreg` 驻留跃迁实验

`V2.7` 揭示了核心规律：以前按整个 Fatbin 一刀切压 `.maxnreg 168` 之所以在 `FB04 / FB05` 上失败，是因为把 `FB04` 中 `255` 寄存器的 `qkv_512` 和 `FB05` 中 `255` 寄存器的 `attention_chained` 一起强行压到了 `168`（引发 `640 B / 176 B` 巨额 spill）！
而根据 `v27/occupancy-baseline.json`，在保持 `qkv_512 (255)` 和 `attention_chained (255)` 为 `.maxnreg 255` 不动的前提下，`FB05`、`FB04` 和 `FB00` 中有一批距离硬件驻留台阶仅差 `8 ~ 36` 个寄存器的核：

### 候选组 1：`FB05 (ViT)` 非 `attention` 核的独立 `.maxnreg 168`（目标：`2 CTA / 8 Warps` → `3 CTA / 12 Warps/SM`，+50% 驻留）
- 保持 `cc_vit_1d_attention_chained_fp8` (`REG=255`) 为 `255` 不动；
- 用 CUDA Occupancy API + `ptxas` 编译实测以下核设为 `.maxnreg 168` 时的真实驻留（注意核实是否存在 `dynamic_shared` 限制 3 CTA 驻留！）与 `STACK` 字节数：
  1. **`cc_vit_1d_ffn_contract_chained_fp8`**（现 `REG = 179`，仅差 `11` regs！每帧 8 次，每 Warp `2,048` HMMA）
  2. **`cc_vit_1d_qkv_chained_fp8`**（现 `REG = 197`，每帧 8 次，每 Warp `1,536` HMMA）
  3. **`cc_vit_1d_ffn_expand_publish_fp8` (`REG = 202`)** 与 **`cc_vit_1d_ffn_expand_chained_fp8` (`REG = 204`)**（共 8 次，每 Warp `2,048` HMMA）
- 请分层测试：① 仅 `contract (179→168)`；② `contract + qkv (179/197→168)`；③ `contract + qkv + expand (→168)`。

### 候选组 2：`FB04 (C512)` 轻/中型核的独立 `.maxnreg 128 / 168`
- 保持 `cc_split_swin_16h_qkv_512_chained_fp8` (`REG=255`) 与 `ffwd_512` (`REG=174`, 256 threads) 为 `255` 不动；
- 编译并查询以下核跨越台阶时的 `STACK` 与真实驻留（含 `dynamic_shared` 校验）：
  1. 256 线程核压 `.maxnreg 128`（`1 CTA / 8 Warps` → `2 CTA / 16 Warps/SM`）：
     - **`cc_split_swin_16h_final_head_512_wait_fp8`**（现 `REG = 136`，仅差 `8` regs！）
     - **`cc_split_swin_16h_proj_512_chained_fp8`**（现 `REG = 141`，仅差 `13` regs！）
  2. 128 线程核压 `.maxnreg 168`（`2 CTA / 8 Warps` → `3 CTA / 12 Warps/SM`）：
     - **`cc_split_swin_16h_proj_pool_512_chained_fp8`**（现 `REG = 180`，仅差 `12` regs！）
     - 以及检查 `ffwd_proj` (`204`) / `ffwd_proj_inpview` (`205`) / `ffwd_inpview` (`212`) 压 `168` 的 `STACK` 代价。

### 候选组 3：`FB00 (C32)` 第 5 核 `upsample_tilesync` (`REG = 212 → 168`)
- 在 `V2.7` 已选 4 核 `168` 基础上，测试将第 5 核 `cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8` (`REG = 212`) 也设为 `168`（升至 `12 Warps/SM`）时的 `STACK` 与整帧耗时变化。

---

## 3. 验收与交付纪律
1. 所有候选必须相对 `V2.7` 保持 **严格 `0 bit-diff`（0 NaN/Inf）**。
2. 在未插桩 `bench_sky.exe` 上完成 720p / 900p / 1080p 三档 50 warmup / 80 iter 正反 ABBA/BAAB 配对实测，只保留带来稳定净提速的组合晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v28.dll`（若均无稳定净收益则如实记录负结果并保持 `V2.7` 为推荐版）。
3. 完整结果写入 `Development/ptx-patcher/v28/README.md`，更新 `DevHistory.md` 与 `WorkingPlan.md`，清理临时大二进制，立即 `git commit`（严禁加 `Co-Authored-By`），不 push。

### V2.8 执行回执（2026-10-28，闇）

两项任务完成，保留上述原任务。[独立审核](doc/性能评估20261028-0335-审核意见.md)及JSON已落盘，原报告未改；[全部实验](ptx-patcher/v28/README.md)。dynamic_shared两档全0、目标理论驻留全部跨台阶，但有限Grid与spill使整帧收益不能由台阶推出。旧全包回退也不是只有两个重核spill。

十项单核/分层三档50/80正反ABBA共240次，无一满足三档双向净提速。pool900/1080快但720慢；up720/1080快但900慢；contract虽零spill，720仍慢0.882%。追加pool＋proj＋up组合24次，下降−0.175%/+0.360%/+0.037%，720方向变号，仍未通过。**本轮不晋升V28 DLL，保持生产推荐V2.7**（SHA256 `28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969`）。

264正式＋11快验，合计275次末帧相对V27严格0bit、maxabs0、invalid0。PTX仅cap变化、基线cubin重编字节一致，受保护核SASS一致，13回归通过。清理临时大文件，保留源码/日志/CSV/JSON；主fast及部署/正式ZIP不覆盖，不push。

### V2.9 实验回执（2026-10-28）

[完整记录](ptx-patcher/v29/README.md)。Unified Mul Pack先纠正lop3 0xd8两个源的顺序后完成GPU原语和两轮三档50/80正反ABBA，共99次运行。A原语及整网0bit，但900/1080收益不稳定，严格默认保留V27。B非0bit，三档PSNR62.609/62.117/60.595dB；两轮三档所有方向均快，复测下降2.598%/2.002%/1.759%，只保留为显式非0bit实验候选。exact/fast DLL保留，临时大缓存清理；未改生产默认、不部署、不push。

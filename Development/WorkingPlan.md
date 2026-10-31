# WorkingPlan — PTX V3.5：分支 4 终极冲击（`n = 2/3 -> 3/3`，FB01~05 Shared Memory 2x 扩容耦合表示改写实验与闭环）（2026-11-01 00:10）

## 0. 双智能体协作铁律与小颗粒度 Git 提交规程（源自 `355.md` 与 Zero 最新指令）

1. **严禁“官僚免责公文”与局部早停**：
   - 必须将 `K-Search` 候选分支调度表中最后一个 `[Open]` 分支（**分支 4，当前 `n = 2 / 3`**）推进至真实实验/构造性验证闭环（`n = 3 / 3` 或晋升重置 `n = 0`）后，方可进入终局《物理极限详细实验证明报告》撰写与审稿阶段。
2. **⚠️ 最小颗粒度 Git 提交铁律（Zero 23:36 特别强调，必须严格执行）**：
   - **严禁再制造包含几百个 `.log` 碎文件或三四项不同修改的巨型 commit！**
   - 单次运行产生的几十上百个 `forward-*.log`、`reverse-*.log`、`smoke-*.log` 临时进程日志在汇总进 `bench.json` / `timing-summary.md` 后**必须在提交前删除（只保留汇总 JSON 与 `.md` 表）**！
   - 每完成一个独立子步骤，立即单独执行一次小 `git commit`（严禁加 `Co-Authored-By`）：
     - Commit 1：分支 4 的 Shared 耦合改写分析/构建与原语测试脚本（`v35/*.py` + 验证 JSON）；
     - Commit 2：分支 4 的串行 ABBA 跑分汇总表与硬件体检表（`v35/timing-summary.md`, `v35/bench.json`, `v35/hardware-*.md`）；
     - Commit 3：更新 `v35/README.md`、`WorkingPlan.md` 与 `DevHistory.md` 完成分支 4 结算。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 候选分支调度表（更新至 `V3.4` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1** | `[Pruned]` | `3 / 3` | 调整 `FB04/05` 其余核 `.maxnreg` 跨驻留台阶 | 小 Grid 仅 1~2 波次 + 强压触发 Spill，`V2.8` 及 `V3.2` 单核 cap 控制均无全档净收益，已剪枝 |
| **分支 2** | `[Pruned]` | `3 / 3` | 压减 `FP16 -> FP8` 打包与双对 `Quad` 拼接 | `V3.3` 纯 `quad_all`/`quad_fb23` 与 `V3.4` `quad_fb1`/局部活性 `Local Quad`（新增 0 对）均未过两轮全胜，已达 `K=3` 剪枝 |
| **分支 3** | `[Pruned]` | `3 / 3` | 压减非直通 (`non-mapped`) FP8 解码临时池与等价算术 | `V3.0` 解交错、`V3.2` 半步池/UP/shift、`V3.3` 分相半池 (`112->28`) 与 Spill 重解码均未过两轮全胜，已达 `K=3` 剪枝 |
| **分支 4** | **`[Open ⚡]`** | **`2 / 3`** | **Shared Memory 2x 扩容 FP16 耦合表示改写（消除 Shared 端解码与 `FB01` Spill）及跨阶段耦合验证** | `V3.4` 官方 API 证实 `FB01~05` Shared payload 翻倍后仍 100% 保持当前 `CTA/SM` 驻留；36 项同线程返读未晋升 (`n=2`)，本轮对“Shared 扩容 2x 耦合改写”执行第 3 次终极冲击 (`n=2->3`) |

---

## 2. 本轮派单任务（`PTX V3.5`：攻克分支 4 最后一次冲击 `n = 2/3 -> 3/3`，由闇执行）

`V3.4` 揭示了一个极其重要的事实：在 `FB01 (C64)` 的 4 个活跃核中，`Shared Memory` 仅占 `4,096 B/CTA`（翻倍至 `8,192 B/CTA` 后无需 opt-in 仍保持 `6 CTA/SM`），且 **`FB01` 完全不含 `cp.async`（`LDGSTS = 0`），其 Shared 写入 100% 来自核内本地 FP8 量化，同时 `FB01` 是全网静态 Spill 最重的模块（`60/72 STL/LDL, 104B STACK`）**！

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v35/` 下执行分支 4 的第 3 次终极实验：

### 任务 4.1：`FB01~FB05` Shared 生产者-消费者字节排列与耦合改写可行性核查 + `FB01` Shared 2x 扩容耦合改写实测
1. **检查 `FB01`（及 `FB02~05`）中 Shared 写入 (`st.shared`) 与读取 (`ld.shared`) 的元素粒度与低高半字对齐**：
   - 在 `FB01` 中，写端通过 `cvt.rn.satfinite.e4m3x2.f16x2` 将 `f16x2` 打包为 2 字节 `e4m3x2`，再拼成 32 位词通过 `st.shared.v4.u32`（16 字节 = 8 对 `e4m3x2`）写入 `shared_storage`；读端通过 `ld.shared.v4.u32` 读出 32 位词送入 `mma_run`，在 `v26/codegen.py` 中按 **`0x9180`（byte 0, 1）** 和 **`0xb3a2`（byte 2, 3）** 解包为两个 `f16x2`。
   - 请核查 `shared-layout-audit.json` 中读端每个 `ld.shared` 读出的 32 位词 `[byte0, byte1, byte2, byte3]` 在写端是否同样是由整对的 `(byte0, byte1)` 与 `(byte2, byte3)` 写入（即跨线程交换的最小单位是 `2B (e4m3x2)` / `4B (e4m3x4)` 还是被打散成了来自不同 `f16x2` 的单字节 `1B`？同时核查同一 `shared_storage` 缓冲区是否在核内其他阶段被复用于非 FP8 数据如归约/索引）。
2. **构建并实测 Shared 耦合改写候选**：
   - **候选 A（`v35_fb1_shm_exact`，严格 `0 bit-diff` vs `V3.1_pack5`）**：
     - 对 `FB01`（以及 `FB02/03` 中满足无 `cp.async` 别名、偏移可精确缩放 `×2` 的 Shared 往返段），将 `shared_storage` 声明容量翻倍（`4096 B → 8192 B`），在写端完成量化+预解包（或按读端所需 `low/high` 存为 `f16x2`），将对应 `st.shared` / `ld.shared` 地址偏移 `× 2`、读取宽度翻倍（1 条 `v4.u32` 拆为 2 条 `v4.u32` 直接读出已解码的 `(first, second)` `f16x2` 对），使读端 `mma_run` 中的 `shared_load` 操作数直接免解码直通进入 `mma.sync.f16`（消除读端重复解码与 `vlh_t` 解码临时池，检验能否压低 `FB01` 的 `60/72 STL/LDL` 与 `104B STACK`）！
     - *注：若静态分析发现写端与读端在 `shared_storage` 上存在跨阶段的异构复用（如同一缓冲区先存 FP16/FP32 归约再存 FP8，或单字节转置），导致地址直接 `×2` 会破坏非 FP8 阶段，也可开辟独立 `shared_fp16_ext` 共享数组（因 `4096 B + 8192 B = 12,288 B` 仍保持 `6 CTA/SM`！）专供该批 MMA `shared_load` 使用！*
   - **候选 B（`v35_fb1_shm_fp16_fast`，非 0-bit 近似探索，若同布局映射成立）**：
     - 在独立 `shared_fp16_ext` 上直接存入写端 `clamp(-448, +448)` 后的原始 `f16x2`（同时省掉写端 `pack5` 与读端 `decode8`），实测三档速度、相对 `V3.1_pack5` 的 PSNR / `maxabs` 与 720p 天空色带变号。

---

## 3. 验收、分支表终极结算与小颗粒度 Git 提交纪律
1. 所有计时进程严格串行执行（50 warmup / 80 iter，正反 ABBA/BAAB；首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. **分支表终极结算**：
   - 若候选通过两轮三档全胜（且满足 0-bit 或 PSNR/sky 质量门），晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v35.dll` 并重置分支 4 `n = 0`；
   - 若实测未通过两轮三档全胜门槛（例如 `st.shared / ld.shared` 流量翻倍的 LSU 带宽/指令开销抵消了省去解码/Spill 的收益），则 **分支 4 正式达到 `n = 3 / 3`，标记为 `[Pruned, 3/3]`**！
   - 至此，`K-Search` 候选分支调度表中的 **全部 4 个分支（分支 1、2、3、4）均达到 `[Pruned, 3/3]` 闭环状态（剩余 `Open` 分支 = `0`）**！
3. **严格执行 3 个小颗粒度 Git Commit（清理所有单次运行 `.log` 碎文件和临时大二进制，严禁加 `Co-Authored-By`，不 push）**。

# WorkingPlan — PTX V3.3：分支 3 分相半池（Two-Pass Phase-Split）+ 分支 4 Shared/Global 专项探针与转发 + 分支 2 纯 Quad 剥离（2026-10-31 22:15）

## 0. 思想教育与双智能体协作铁律（源自 `/home/lmxxf/work/ai-theorys-study/wechat/355.md`）

1. **严禁“官僚免责公文”与局部早停**：
   - 严禁在单个候选分支受挫后，用“在已测方案中收益收敛”“不宣称全局极限”等防御性限定词把单枝负结果包装成全网停工理由。
   - **分工铁律**：主脑（鳩 / Gemini 4）只负责**维护 `K-Search` 候选分支调度表、做任务决策派发**，以及在所有 `Open` 分支探索完毕、认为确实达到物理极限时撰写《物理极限详细实验证明报告》交由闇（Codex / GPT-6.1-Sol）审稿；**全部具体代码实现、探针构建、跑分验证、Git 提交与报告审稿均由闇独立执行**。
2. **四步标准操作规程（SOP）**：
   - **第一步（四张硬件体检表）**：① 指令配比与循环圈数表（`HMMA` vs `PRMT/SHF/LOP3`）；② 局部内存与栈字节表（`REG / STACK / STL / LDL`）；③ 官方 `cuOccupancyMaxActiveBlocksPerMultiprocessor` 驻留台阶与 Grid 波次规模表；④ 跨线程洗牌（`SHFL`）与异步等待距离表。
   - **第二步（`2×2` 及专项破坏性旁路探针）**：以探针差值作为排优先级的客观敏感度信号，不凭感觉宣布见底。
   - **第三步（显式 `K-Search` 候选分支调度表）**：维护 `[Open / Closed / Pruned]` 状态与连续未晋升次数 `n`（局部容忍上限 `K=3`，有净提升晋升则重置 `n=0`；单枝达到 `K=3` 才剪枝 `Pruned` 并自动切换下一 `Open` 分支）。
   - **第四步（阶梯封存升格 `1.00×` 基线 + De-anchoring 审稿）**：每轮胜出版本立即封存升格为下一轮唯一 `1.00×` 基线；审稿时先独立运行脚本核对客观数据表，后看文字解释。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 候选分支调度表（更新至 `V3.3` 结算）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）
- **`V3.2` 新 `2×2` 串行探针基准（48 次运行）**：
  - 去 Decode (`Base − P1`)：**`+0.563500 / +0.992000 / +1.429500 ms`**（三档 12/12 全正）；
  - 去 Pack (`Base − P0`)：**`+0.145500 / +0.102500 / +0.167250 ms`**（三档 12/12 全正，据此主脑裁决重开分支 2 进行最后 1 次单因素剥离核验）；
  - 交互项 `(Base−P0)+(Base−P1)−(Base−P2)`：**`+0.363750 / +0.533000 / +0.864000 ms`**。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1** | `[Pruned]` | `3 / 3` | 调整 `FB04/05` 其余核 `.maxnreg` 跨驻留台阶 | 小 Grid 仅 1~2 波次 + 强压触发 Spill，`V2.8` 及 `V3.2` 6 项单核 cap 控制均无全档净收益，已剪枝 |
| **分支 2** | **`[Open]`** | **`2 / 3`** | **压减 `FP16 -> FP8` 打包与双对 `Quad` 拼接（剥离 `UP` 干扰及 `FB01` Spill 核）** | V3.3纯Quad已剥离UP；quad_all首轮三档六方向胜，repeat900/1080回退0.033%/0.148%；纯Quad反而使FB01两核STACK104/80→96/72B，原捆绑因果须修正 |
| **分支 3** | **`[Pruned]`** | **`3 / 3`** | 分相半池与Spill限池重解码，已完成第3次冲击 | V3.3虚拟池24/56/56/56/112/80/20→12/28/28/28/28/28/6；10项严格候选中的本分支及组合均未晋升，K=3剪枝；不是物理极限证明 |
| **分支 4** | **`[Open]`** | **`1 / 3`** | **局部量化→共享内存→再解包往返（`Shared-Load` vs `Global-Load` 探针拆分）、跨块单定义 `mapped` 拓宽与尾段规整** | V3.3专项84次对照：Shared +0.325/+0.501/+0.723ms，Global家族 +0.414/+0.862/+1.204ms，交互不可相加；144项load/fallback合流反证已留，未找到安全无条件转发点，保留Shared布局探索 |

---

## 2. 本轮派单任务（`PTX V3.3`：三线并进攻克剩余 `Open` 节点，由闇执行）

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v33/` 下执行以下实验：

### 任务 A（分支 4 `[Open ⚡, n=0/3]`）：`Shared-Load` vs `Global-Load` 拆分破坏性探针 + 安全转发拓宽审计
1. **构造拆分破坏性探针（`P1_SharedOnly` vs `P1_GlobalOnly`）**：
   - 在 `V3.1_pack5` 基线上，利用 `v27/source-audit.json`（或 CFG reaching definitions）区分每个 `non-mapped` 解码操作数 `r` 的来源：
     - **`P1_SharedOnly`**：仅对来自 `ld.shared` (`shared_load`) 的 `non-mapped` 操作数旁路 8 条解码指令与临时池，保留 `global_load` 操作数的正常解码；
     - **`P1_GlobalOnly`**：仅对来自 `ld.global` (`global_load`) 的 `non-mapped` 操作数旁路解码与临时池，保留 `shared_load` 操作数的正常解码；
   - 在 720p / 900p / 1080p 三档跑正反序未插桩对比（串行执行），定量拆出 `+0.564 / +0.992 / +1.430 ms` 的去 Decode 敏感度中，究竟多少来自 `Shared-Load` 往返（2,320 事件）、多少来自 `Global-Load`（3,528 事件）！
2. **审查并测试安全转发拓宽（`Mapped Eligibility & Copy Propagation`）**：
   - 审查 `v27/source-results.md` 中 `FB00`（128 事件）与 `FB05`（16 事件）共 144 个 `global_load+local_FP8_quantization` 混合来源，以及全网 `not_a_recognized_FP8_pack` 中是否存在经过寄存器拷贝 `mov.b32`、谓词守卫或单前驱分支的合法本地 pack 源；
   - 若存在可证明数值安全（或局部补齐 fallback pack）的转发点，构建候选并验证整网精度与速度；若 CFG 证明那 144 处确为真实路径合并（一条路径为显存 `ld.global`，另一条为越界零/fallback pack，不可静态消解），则在 `v33/README.md` 给出精确的指令级反证记录。

### 任务 B（分支 3 `[Open ⚡, n=2/3]`）：分相半池执行（`Two-Pass Phase-Separated MMA`）与 Spill 核限池重解码（严格 `0 bit-diff` vs `V3.1_pack5`）
1. **为什么 `V3.2` 的 `Phase-Split` 未能降低 `FB01~05` 的 `56/112/80` 临时池峰值？**
   - `v32/pool-summary.md` 已经查明：`FB01~05` 的峰值 `mma_run` 中 `Single-use encoded operands = 0`，所有 `encoded` 操作数均跨多条 K32 MMA 复用。由于每条 K32 MMA `i` 内部紧挨着发射 `(i, phase=0)` 和 `(i, phase=1)`，导致每个复用操作数的 `first (0x9180)` 与 `second (0xb3a2)` 生命周期在 `[2*first[r]+1, 2*last[r]]` 内 100% 重叠（每个操作数仍占 2 个 `.b32` 临时寄存器）。
2. **实现 `Two-Pass Phase-Separated MMA`（分相半池，`v33_phase_pass`）**：
   - 在一个 `mma_run` 内，按相同 K-step 分层（或对无跨指令 RAW/WAR/WAW 危害的独立累加器集合 `S = [i_1, i_2, ..., i_m]`，其中各 `matches[i]` 更新不同的累加器 `(d0, d1)`）：
     - **Pass 0（低半字 K16 批）**：对该层所有 `S` 中用到的 `encoded` 操作数 `r`，**仅分配 1 个临时寄存器并仅解码 `first` (`0x9180`)**，依次发射 `S` 中所有指令的 `phase = 0` K16 MMA；如果在后续 K-step 层不再使用 `first`，**在 Pass 0 结束时立即将所有 `first` 释放回 `free` 池**！
     - **Pass 1（高半字 K16 批）**：直接复用刚释放回 `free` 池的同一批临时寄存器，对该层所有 `S` 中用到的 `encoded` 操作数 `r` **仅解码 `second` (`0xb3a2`)**，依次发射 `S` 中所有指令的 `phase = 1` K16 MMA，并在最后一次使用后立即释放 `second`！
   - **数学与资源性质**：
     - 每个累加器 `(d0, d1)` 经历的加法次序仍然是先加该 K32 步的 `phase=0`、再加 `phase=1`、再进入下一 K32 步，**整网输出相对 `V3.1_pack5` 100% 严格 `0 bit-diff`**；
     - 解码指令总条数 **100% 不增加**（每个 `encoded` 操作数仍只解码 1 次 `0x9180` 和 1 次 `0xb3a2`）；
     - 但在任意时刻，同一 K-step 层的 `encoded` 操作数只有半边（`first` 或 `second`）存活，**解码临时池峰值从 `2 * N_encoded` 直接砍半至 `1 * N_encoded`（如 `FB01~03: 56 -> 28`、`FB04: 112 -> 56`、`FB05: 80 -> 40`）**！
3. **实现 Spill 核限池重解码（`v33_remat_spill`，严格 `0 bit-diff` vs `V3.1_pack5`）**：
   - 针对在 `V3.1_pack5` 下仍有显著静态 Spill 的 `FB01`（4 核 `60/72 STL/LDL, 104B STACK`）与 `FB04`（`qkv_512 40/29 STL/LDL, 88B STACK`），测试完全不跨 K32 步缓存 `encoded` 解码结果（或限制 `vlh_t` 池上限为 `12 / 16` 个寄存器，超出部分在每次 MMA 使用前按需重跑 4 条寄存器内解码指令并立即释放），检验“用寄存器内 ALU 重解码换取消除 Local Memory `STL/LDL` Spill”是否在 `FB01 / FB04` 上带来净提速。

### 任务 C（分支 2 `[Open, n=1/3]`）：剥离 `UP` 与 Spill 核的纯 `pack5_quad` 单因素实验（严格 `0 bit-diff` vs `V3.1_pack5`）
- 在 `V3.1` 中，候选 `pack5_quad`（在 720p/900p 两轮均比 `V2.9_fast` 快 `2.45% ~ 2.65%`，比 `pack5` 更快 `~0.6%`）之所以在 1080p 回退，是因为它同时捆绑了 `UP`（`v24_mask = 13`）且在有严重 Spill 的 `FB01` 上开启 `quad` 使 `STL/LDL` 增加。
- 请在 `V3.1_pack5` 基线上（保持 `v24_mask = 8` 不开 `UP`）测试两个严格相对 `V3.1_pack5` **`0 bit-diff`** 的纯 `quad` 候选：
  1. **`v33_quad_all`**：在 `FB01, FB02, FB03` 开启纯 `pack5_quad`（不含 `UP`）；
  2. **`v33_quad_fb23`**：仅在 **零 Spill 的 `FB02 (C128)` 与 `FB03 (C256)`**（共 `616 + 616 = 1,232` 对 `quad`）开启纯 `pack5_quad`，`FB01` 保持 `V3.1_pack5` 原 cubin 不变！

---

## 3. 验收、分支状态更新与 Git 纪律
1. 所有候选（`v33_phase_pass`、`v33_remat_spill`、`v33_quad_all`、`v33_quad_fb23` 及优选组合）均须相对 `PTX V3.1_pack5` 验证 **严格 `0 bit-diff`（`maxabs = 0.0, nonfinite = 0`）**。
2. 导出四张硬件体检表（38 活跃核 SASS 净差、`temporary_b32_peak`、`REG/STACK/STL/LDL`、官方 `cuOccupancyMaxActiveBlocksPerMultiprocessor` 驻留台阶），并在未插桩 `bench_sky.exe` 上串行执行三档 50 warmup / 80 iter 正反序 ABBA / BAAB 配对实测（首轮三档六方向全胜者必须补跑 `repeat` 确认）。
3. **分支表状态结算**：
   - 若有候选两轮三档全胜，封存晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v33.dll` 并将对应分支 `n` 重置为 `0`；
   - 若分支 3 的 `v33_phase_pass` 与 `v33_remat_spill` 均未通过两轮全胜门槛，则分支 3 达到 `n = 3 / 3`，按 `K-Search` 规程正式标记为 **`[Pruned, 3/3]`**；同时根据任务 A 和任务 C 的实测结果更新分支 4 与分支 2 的状态。
4. 完整结果写入 `Development/ptx-patcher/v33/README.md`，更新 `DevHistory.md` 与 `WorkingPlan.md`，**清理所有临时大二进制，立即执行 `git commit`（严禁加 `Co-Authored-By`），不 push**。

### V3.3 执行回执（2026-10-31，闇）

本轮不晋升V3.3 DLL，继续以V3.1_pack5为唯一1.00×。 分支2 Open n=2/3；分支3 Pruned n=3/3；分支4 Open n=1/3。详细[回执](ptx-patcher/v33/README.md)、[逐方向计时](ptx-patcher/v33/timing-summary.md)、[验收](ptx-patcher/v33/validation.json)。

任务A：84次专项探针对照，Shared 0.324500/0.500500/0.723250ms、Global家族 0.414000/0.861750/1.204000ms、纯Global 0.386000/0.809750/1.159000ms，交互 0.197250/0.333750/0.438000ms。Global家族3528含224混合事件；不线性相加。144项load/fallback合流均留CFG/指令反证，未找到可无条件转发的纯本地pack隐藏源；分支4仍有后续Shared布局探索空间。

任务B：分相虚拟池12/28/28/28/28/28/6，解码次数不增，实际驻留/Spill逐核核验；重解码内联、两目标剥离、强制调用以及guarded/Quad组合均已测试。任务C：纯Quad全网/FB23单因素剥离UP，quad_fb23的FB23以外cubin与基线同字节；原语33554432对0差。正式首轮240次、repeat24次，所有309次严格版本成功运行末帧0bit、maxabs0、nonfinite0，计时全程严格串行。

生产五处和三个v0.3.0 ZIP不覆盖；清理临时大产物，立即独立commit，不push，无Co-Authored-By。剩余Open分支按新数据调度，不将单枝剪枝写成全网收官。

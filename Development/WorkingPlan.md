# WorkingPlan — PTX V3.4：分支 2（FB01 独立 Quad 与局部基本块 Quad）与分支 4（36 项 `pack_multidef` CFG 可达定义转发与 Shared 配对审计）终极闭环（2026-10-31 23:00）

## 0. 双智能体协作铁律与四步规程（源自 `/home/lmxxf/work/ai-theorys-study/wechat/355.md`）

1. **严禁“官僚免责公文”与局部早停**：
   - 在 `K-Search` 候选分支调度表中尚有 `[Open]` 分支未完成闭环验证前，严禁提前撰写“已达物理极限”报告。
   - **分工铁律**：主脑（鳩 / Gemini 4）负责维护 `K-Search` 候选分支调度表、做任务决策派发，并在全部 `Open` 分支闭环后撰写《达到物理极限的详细实验报告》交由闇（Codex / GPT-6.1-Sol）审稿；**全部具体代码实现、探针构建、跑分验证、Git 提交与报告审稿均由闇独立执行**。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 候选分支调度表（更新至 `V3.3` 后）

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1** | `[Pruned]` | `3 / 3` | 调整 `FB04/05` 其余核 `.maxnreg` 跨驻留台阶 | 小 Grid 仅 1~2 波次 + 强压触发 Spill，`V2.8` 及 `V3.2` 单核 cap 控制均无全档净收益，已剪枝 |
| **分支 2** | **`[Pruned]`** | **`3 / 3`** | **压减 `FP16 -> FP8` 打包与双对 `Quad` 拼接（`FB01` 独立 `Quad` 与基本块局部死分析 `Local Quad` 拓宽）** | V3.4 FB01独立Quad首轮全胜，repeat720/1080回退、900变号；Local精确规则新增0对；本分支K=3剪枝 |
| **分支 3** | `[Pruned]` | `3 / 3` | 压减非直通 (`non-mapped`) FP8 解码临时池与等价算术 | `V3.0` 解交错重排、`V3.2` 半步池/UP/shift、`V3.3` 分相半池 (`112->28`) 与 Spill 重解码累计 20+ 候选均未两轮全胜，已达 `K=3` 剪枝 |
| **分支 4** | **`[Open]`** | **`2 / 3`** | **`36` 项 `pack_multidef` 的 CFG 单一可达定义转发、Shared 局部量化存取配对审计与尾段规整** | V3.4全部36项均双可达定义；Shared payload翻倍官方API仍保持当前驻留，容量否定前提不成立；36向量编码词返读候选已测未晋升，耦合FP16表示路径未排除，不能终局剪枝 |

---

## 2. 本轮派单任务（`PTX V3.4`：分支 2 与分支 4 终极闭环攻坚，由闇执行）

请严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v34/` 下执行以下实验：

### 任务 A（分支 2 终极冲击 `[Open ⚡, n=2/3 -> 3/3]`）：`FB01` 独立 `Quad` + 基本块级局部 `Local Quad` 拓宽（严格 `0 bit-diff` vs `V3.1_pack5`）
1. **单模块剥离候选 `v34_quad_fb1`（仅在 `FB01` 启用纯 `pack5_quad`）**：
   - `V3.3` 揭示了一个反直觉事实：`quad_all` (`FB01+02+03`) 让 `FB01` 的两个活跃核 `STACK` 从 `104/80 B` 降至 **`96/72 B`**、全网 `STL` 从 `107 → 106` 且首轮三档全胜，而去掉 `FB01` 的 `quad_fb23` 反而首轮失败。这说明 **`FB01` 才是 `quad` 的正向受益模块**，而 `FB02/03` 零 Spill 核上的 `quad` 可能拖累了 1080p `repeat`！
   - 请单独构建并测试 **`v34_quad_fb1`**（仅 `FB01` 使用 `mask=12` 纯 `pack5_quad`，其余 14 个 Fatbin 保持 `V3.1_pack5` 原 cubin 逐字节不变）。
2. **基本块级局部死变量分析拓宽 `Quad`（`v34_quad_local` 与 `v34_quad_fb0145`）**：
   - 审查为什么 `v24/codegen.py` 的 `fuse_quads` 在全网 `7,540` 个 `mov.b32 %dst, {%lo, %hi}` 中只融合了 `1,688` 对（`FB00, FB04, FB05, FB06` 全为 `0` 对）：
     - 原 `fuse_quads` 第 46 行要求 `counts[lo] == 2 and counts[hi] == 2 and len(downs[lo]) == 1 and len(downs[hi]) == 1`（即要求 `.b16` 临时寄存器 `%rsXX` 在**整个几千行的函数内**全局只定义 1 次、使用 1 次，且第 53 行要求词法花括号深度 `depth == 1`）！一旦编译器在不同循环迭代或不同块复用了同一个 `%rsXX` 名字，或位于内层作用域，`fuse_quads` 就全部拒绝。
   - 请编写精确的**同基本块局部活性检查（Block-Local Liveness Check）**：
     - 对每个无谓词守卫的 `pack`（`mov.b32 %dst, {%lo, %hi}`），在同一基本块内向上查找紧邻前方的最后一次 `lo` 定义 `a`（`cvt.rn.satfinite.e4m3x2.f16x2 %lo, %src_lo`）与 `hi` 定义 `z`（`cvt.rn.satfinite.e4m3x2.f16x2 %hi, %src_hi`）；
     - 只要满足：① `a, z, pack` 位于同一基本块且无谓词守卫；② 在 `min(a, z)` 与 `pack` 之间，`%src_lo, %src_hi, %lo, %hi` 未被其他指令覆写，且 `%lo, %hi` 未被中间指令读取；③ **在 `pack` 之后，沿着 CFG 所有可达路径，`%lo` 和 `%hi` 在被下一次重新定义（Overwrite）或函数返回（`ret`/`exit`）之前没有任何读取（Locally Dead after `pack`）**，即可 100% 安全地融合为 `pack5_quad`（在 `pack` 之后 `%lo, %hi` 已死，无需写出 16 位半字）！
   - 请审计该精确局部活性规则在 `FB00..FB06` 38 个活跃核中能新增解锁多少对 `quad`，检查其对 `FB00/01/04/05` 静态 SASS、`PRMT`、`REG` 与 `STACK` 的影响，并对全网 `v34_quad_local` 及仅在降低 `STACK/REG` 模块开启的精选组合做三档 50/80 正反序 ABBA 实测。

### 任务 B（分支 4 终极闭环 `[Open ⚡, n=1/3 -> 3/3]`）：`36` 项 `pack_multidef` 的 CFG 单一可达定义审计与 Shared 本地量化读写配对闭环
1. **审计 38 活跃核中的 `36` 项 `pack_multidef`（`Single Reaching Pack Definition Audit`）**：
   - `v33/README.md` 指出：在 5,848 个 `non-mapped` 事件中，有 `5,812` 项是 `not_a_recognized_FP8_pack`，另有 **`36` 项是 `pack_multidef`**（即目标寄存器在函数内有多处定义，被 `multidef` 保守排除）。
   - 请用 CFG 可达定义分析逐一检查这 `36` 项 `pack_multidef`：
     - 在到达该 `mma_run` 入口的控制流图上，实际能夠到达（Reaching）的定义有几条？
     - 是否存在“虽然函数内別处重用了该寄存器名，但到达当前 `mma_run` 的唯一可达定义是一条 100% 合法的本地 `FP8 pack`（且其 `low, high` 源在 `mma_run` 前未被覆写）”的情况？或者到达的複数定义是否实际上不可静态区分（如循环回边更新 vs 初始值）？
     - 若存在可证明 100% 严格等价（`0 bit-diff`）的安全转发项，构建候选并实测；若 CFG 证明这 36 项在到达 `mma_run` 时均存在多条不同运行时值的可达定义（如循环携带依赖或分支合流），请输出 `v34/multidef36-audit.json` 逐项给出指令行号与可达定义集证明。
2. **审计 `FB01~FB05` Shared Memory 本地量化写入 (`st.shared`) 与解码读出 (`ld.shared`) 的跨线程映射关系（`Shared-Memory Producer-Consumer Layout Audit`）**：
   - 针对 `2,320` 个 `shared_load` 解码事件，编写静态分析脚本核查 `FB01~FB05` 中写入同一 Shared 符号的 `st.shared` 指令与读取它的 `ld.shared` 指令：
     - 统计每个模块中：① Shared 缓冲区总大小与剩余可用 Shared 容量（对比 `101,376 B/SM` 与当前 `CTA/SM` 驻留）；② 写端线程的地址表达式与读端线程的地址表达式是否存在**跨线程矩阵转置 / 重排（Cross-Lane Permutation）**，以及在 `FB02~FB05` 中是否与 `cp.async` 硬件异步拷贝共用同一块 Shared 缓冲区；
     - 给出客观的架构级可判定结论（保存在 `v34/shared-layout-audit.json`）：在不改变模型算法与 Shared 容量驻留的前提下，静态 PTX 层能否在不触发 Shared 容量翻倍降驻留或破坏 `cp.async` 布局的情况下直接消除 Shared 端的 FP8 打包/解包？若存在可无损消除的同线程/同布局局部往返，立即实现并实测；若全部涉及跨线程转置或与 `cp.async` 耦合且扩容 FP16 会突破 Shared 驻留上限，则给出逐模块字节与指令级证明，将分支 4 正式推进至闭环状态。

---

## 3. 验收、分支状态结算与 Git 纪律
1. 所有生产候选必须相对 `PTX V3.1_pack5` 验证 **严格 `0 bit-diff`（`maxabs = 0.0, nonfinite = 0`）**，所有计时进程严格串行（50 warmup / 80 iter，正反 ABBA/BAAB，首轮三档六方向全胜必须补跑 `repeat` 确认）。
2. 输出四张硬件体检表、`v34/multidef36-audit.json`、`v34/shared-layout-audit.json` 与 `v34/README.md`。
3. **分支表终极结算**：
   - 若有候选两轮三档全胜，晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v34.dll` 并重置对应分支 `n = 0`；
   - 若本轮全部候选均未通过两轮三档全胜门槛，且 `multidef36` 与 `shared-layout` 审计证实无剩余静态无损可兑现路径，则分支 2 与分支 4 均正式结算为 **`[Pruned, 3/3]`**（此时 `K-Search` 表中 4 个分支全部闭环，剩余 `Open` 分支为 `0`，移交主脑撰写终局《达到物理极限的详细实验证明报告》交闇审稿）。
4. 更新 `DevHistory.md` 与 `WorkingPlan.md`，**清理所有临时大二进制，立即执行 `git commit`（严禁加 `Co-Authored-By`），不 push**。

### V3.4 执行回执（2026-11-01，10月31日晚启动）

V3.4无晋升候选，保留V3.1_pack5 SHA1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86为唯一1.00×。 分支2 Pruned3/3；分支1/3保持Pruned3/3；**分支4保持Open2/3，剩余Open=1，终局交接条件不成立。** [完整回执](ptx-patcher/v34/README.md)、[验收](ptx-patcher/v34/validation.json)。

5个严格候选首轮120次，仅quad_fb1全档双向胜出，补24次repeat未通过；加18快验共162次末帧0bit/maxabs0/nonfinite0，所有计时串行。Local规则真正实现并通过结构/GPU控制，但新增融合对0；36项multidef均两条可达定义。完整Shared库存另解锁36个编码词返读（9入口），保留量化与形状回退，独立及FB01 Quad组合均实测。

**新事实推翻闭环前提：102400B/SM与101376B/block opt-in不可混同。实际baseline cubin加倍payload后，FB01～05官方API均保持当前CTA/SM。** 不能用容量证明所有剩余改写不可兑现。保留量化边界并成对改写Shared生产者/消费者及异步拷贝布局的方向仍未排除，不能将两项审计机械计作两次失败而强迫分支4变成Pruned3/3。

本轮已完成规定单因素、Local实现、CFG与Shared容量/布局审计及安全局部候选实测；没有编造“全部闭环”或物理极限结论。生产部署/ZIP不覆盖；清理临时大产物并立即独立commit，不push，无Co-Authored-By。

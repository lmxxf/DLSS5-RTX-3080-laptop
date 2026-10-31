# WorkingPlan — 贯彻《355.md》四步防早停规程与 PTX V3.2 分支 3（Decode 压减与半步生命周期池）攻坚（2026-10-31 21:45）

## 0. 思想教育与双智能体协作铁律（源自 `/home/lmxxf/work/ai-theorys-study/wechat/355.md`）

1. **严禁“官僚免责公文”与局部早停**：
   - 严禁在单个候选分支受挫后，用“在已测方案中收益收敛”“不宣称全局极限”等防御性限定词把单枝负结果包装成全网停工理由。
   - **分工铁律**：主脑（鳩 / Gemini 4）只负责**维护 `K-Search` 候选分支调度表、做任务决策派发**，以及在所有 `Open` 分支探索完毕、认为确实达到物理极限时撰写《物理极限详细实验证明报告》交由闇（Codex / GPT-6.1-Sol）审稿；**全部具体代码实现、探针构建、跑分验证、Git 提交与报告审稿均由闇独立执行**。
2. **四步标准操作规程（SOP）**：
   - **第一步（四张硬件体检表）**：① 指令配比与循环圈数表（`HMMA` vs `PRMT/SHF/LOP3`）；② 局部内存与栈字节表（`REG / STACK / STL / LDL`）；③ 官方 `cuOccupancyMaxActiveBlocksPerMultiprocessor` 驻留台阶与 Grid 波次规模表；④ 跨线程洗牌（`SHFL`）与异步等待距离表。
   - **第二步（`2×2` 破坏性旁路探针）**：以探针差值作为排优先级的客观敏感度信号，不凭感觉宣布见底。
   - **第三步（显式 `K-Search` 候选分支调度表）**：维护 `[Open / Closed / Pruned]` 状态与连续未晋升次数 `n`（局部容忍上限 `K=3`，有净提升晋升则重置 `n=0`；单枝达到 `K=3` 才剪枝 `Pruned` 并自动切换下一 `Open` 分支）。
   - **第四步（阶梯封存升格 `1.00×` 基线 + De-anchoring 审稿）**：每轮胜出版本立即封存升格为下一轮唯一 `1.00×` 基线；审稿时先独立运行脚本核对客观数据表（38 活跃核 SASS 净差/资源表、正反序 ABBA 原始数据、探针与分支表剩余 `Open` 节点），后看文字解释。

---

## 1. 当前唯一 `1.00×` 封存基线与 `K-Search` 候选分支调度表

- **当前唯一 `1.00×` 对比基线**：**`PTX V3.1_pack5`**（`v0.3.0` 生产版，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`，`266,414,592 B`，15/15 原槽位 `O4`，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）
  - 38 个活跃 FP8 核（`FB00..FB06`）静态账本：`INSN_NONOP = 152,076`（`INSN_WITH_NOP = 152,807`），`HMMA = 13,188`，`PRMT = 19,861`，`STL/LDL = 107/108`。
  - `2000` 轮正交探针基准：去 Decode（`V3.1_pack5 − P1_V31_NoDec`）在未插桩（`+0.574 / +0.925 / +1.363 ms`）与 NVAPI（`+0.578 / +0.887 / +1.984 ms`）全部 18 个 pass 中 100% 为正，其中 **`74.79% / 72.01% / 80.11%`** 集中在 30 个零静态 Spill 核（`G1` 23 个 API 驻留不变核 + `G2` 7 个 API 驻留跨阶核）。

### 候选分支调度表（`K = 3`）

| 分支编号 | 状态 | 连续未晋升 `n` | 优化分支假设与机制靶点 | 探针敏感度与历史依据 |
| :--- | :---: | :---: | :--- | :--- |
| **分支 1** | `[Pruned]` | `3 / 3` | 调整 `FB04/05` 其余核 `.maxnreg` 跨驻留台阶 | 小 Grid 仅 1~2 波次 + 强压触发 Spill，`V2.8` 11 项控制测满无全档净收益，已剪枝 |
| **分支 2** | `[Closed]` | `0 / 3` *(已晋升)* | 压减 `FP16 -> FP8` 打包算术指令（`13 -> 9 -> 5` 条 SASS） | `V2.7 P0 +0.57ms` -> `V2.9_fast` -> `V3.1_pack5` 连续两代晋升后，未插桩 900/1080p `V31 - P0` 均值变号，阶段收官；V3.2新P0三档12/12正，需主脑复核是否重开 |
| **分支 3** | **`[Open ⚡]`** | **`2 / 3`** | **压减非直通 (`non-mapped`) FP8 解码指令、半步 (`Phase-Split`) 临时池与独立 `UP` 解码** | `V3.1 P1_NoDec` 未插桩 `+0.574 / +0.925 / +1.363 ms`（18/18 为正，约 75%~80% 在 `G1+G2` 零 Spill 核）；`V3.0` 及本轮 `V3.2` 均未晋升 (`n=2`)，**当前第一优先级** |
| **分支 4** | **`[Open]`** | **`0 / 3`** | **局部量化→共享内存→再解包往返（Local Pack->STS->LDS->Unpack）与尾段/同步规整** | `v27/source-audit.json` 显示 `FB01~05` 存在本地量化写 Shared 后再作为 non-mapped 读出解包的往返路径，待构造专项探针与实验，排队候补 |

---

## 2. 本轮派单任务（`PTX V3.2`：攻克 `分支 3 [Open ⚡]`，由闇执行）

请闇先阅读 `/home/lmxxf/work/ai-theorys-study/wechat/355.md` 同步四步规程，然后严格以 **`PTX V3.1_pack5`**（SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`）为唯一 `1.00×` 基线，在 `Development/ptx-patcher/v32/` 下对 **分支 3（Decode 路径）** 开展系统性探针与候选实验：

### 靶点 3.1：半步按需解码与半步即时释放（`Phase-Split JIT Decode`，严格 `0 bit-diff` vs `V3.1_pack5`）
- **现有问题诊断**：在 `v26/codegen.py` 中，每个 `encoded`（`non-mapped`）操作数 `r` 在 `when[r] == i`（第 `i` 条 K32 MMA 之前）一次性分配 **2 个 `.b32` 临时寄存器 `(first, second)`** 并同时发射 `0x9180` 与 `0xb3a2` 共 8 条解码指令，且直到 `last[r] == i` 的 `phase = 0, 1` 两条 K16 MMA 全部执行完后才一起释放。
  - 这导致：① 所有单次使用操作数（`first[r] == last[r]`）本可在 `phase=0` MMA 结束后立即释放 `first` 并在 `phase=1` 复用同一个寄存器解码 `second`（峰值从 2 格降为 1 格）；② 跨步复用操作数在 `last[r]` 的 `phase=0` MMA 跑完后，`first` 已经死亡却仍占着寄存器直到 `phase=1` 结束。
- **实现要求**：
  - 将 `v26/codegen.py` 的解码与释放粒度从 K32 步 `i` 细化为半步 `step = 2*i + phase`（注意严格检查 `r` 是否在 `phase=0` 被当前 MMA 的 `d0/d1` 覆写：若 `r in (m['d0'], m['d1'])` 或被更早的 `d0/d1` 覆写，则在覆写发生前的 `step` 提前解码 `second`；否则 `first` 在首次读取的 `2*first[r]` 步解码、在末次读取的 `2*last[r]` 步结束后立即 `free.append(first)`，而 `second` 在首次读取的 `2*first[r]+1` 步才从 `free` 池分配并解码、在 `2*last[r]+1` 步结束后立即释放）。
  - 统计 38 个活跃核的解码临时池峰值 `temporary_b32_peak`、编译后的 `REG / STACK / STL / LDL`、以及 `cuOccupancyMaxActiveBlocksPerMultiprocessor` 是否有 `G2` 核（如 `FB05 ffwd_expand_publish 172 regs`、`FB04 proj_512 141 regs`、`final_head_512 136 regs`）跨过 `168 / 128 regs` 驻留台阶！

### 靶点 3.2：独立 `cvt.rn.f16x2.e4m3x2` 升级为 5-PTX `v24.up`（在 `V3.1_pack5` 基线上单因素剥离，严格 `0 bit-diff` vs `V3.1_pack5`）
- **现有问题诊断**：在 `V3.1_pack5` 中，`v24_mask = 8`（未开启 bit 1），导致全网 4,744 处非 MMA 独立 `cvt.rn.f16x2.e4m3x2` 仍在使用 `build_sm86_dlls.py` 中 7 条指令、3 个临时寄存器的旧版 `fast_fp8_pair_to_half_lines`（`V3.1` 的候选 `C` 将 `quad` 和 `up` 绑在一起测试，未在 `pack5` 上单独测试 `up`）。
- **实现要求**：在 `V3.1_pack5` 基线上单独测试开启 `v24.up`（`v24_mask = 9`，即将独立 `cvt.rn.f16x2.e4m3x2` 替换为 `prmt 0x9180 + and 0x017f017f + shl 7 + mul 0x5c005c00`），审计 38 个活跃核的静态 SASS 净差、`PRMT / LOP3 / SHF` 变化与 `REG / STACK` 变化。

### 靶点 3.3：MMA 内部 `non-mapped` 解码算术序列与 `G2` 临界核（距 `168/128 regs` 仅差 `4~13` 寄存器）专项突破
- 检查 `v26/codegen.py` 的 `decode(register, first, second)` 在 `ptxas -O4` 下的 SASS 生成：
  1. 检查 `mul.rn.f16x2 {dst}, {dst}, 0x5c005c00;`（直接写浮点/位立即数 vs 预装 `dlssnr_fp8_scale` 寄存器）或其他等价/近似无偏解码序列能否进一步减少每对解码的 SASS 指令数或寄存器占用；
  2. 针对 `G2` 组中在 `V3.1_pack5` 下距离 `3 CTA/SM (168 regs)` 或 `2 CTA/SM (128 regs)` 仅差 `4 ~ 13` 个寄存器的零 Spill 核（特别是 `FB05` 的 `ffn_expand_publish 172 regs`、`ffn_contract_chained 179 regs`、`ffn_expand_chained 180 regs` 与 `FB04` 的 `final_head_512 136 regs`、`proj_512 141 regs`、`proj_pool_512 180 regs`），检查在结合靶点 3.1 / 3.2 后它们的 `REG` 下降情况，并验证此时是否自然跨阶或仅需极小代价即可跨阶。

---

## 3. 验收与交付纪律
1. **原语与整网精度校验**：所有保持语义的候选（如 3.1、3.2）必须相对 `PTX V3.1_pack5` 保持 **严格 `0 bit-diff`（`maxabs = 0.0, nonfinite = 0`）**；若测试任何近似解码候选，必须先过 33,554,432 对 GPU 原语验证并报告相对 `V3.1_pack5` 及 `V1` 的 PSNR / `maxabs` / 天空色带变号。
2. **四张体检表与正反序 ABBA 实测**：
   - 导出各候选在 38 个活跃核上的静态 SASS 账本（`INSN_NONOP`, `INSN_WITH_NOP`, `HMMA`, `PRMT`, `STL/LDL`, `REG`, `STACK`）及官方 `cuOccupancyMaxActiveBlocksPerMultiprocessor` 驻留表；
   - 在未插桩 `bench_sky.exe` 上对各单因素及优选组合执行 720p / 900p / 1080p 三档 50 warmup / 80 iter 正反序 ABBA / BAAB 配对实测（若首轮胜出，必须补跑一轮 `repeat` 确认！）。
3. **分支状态更新与 Git 纪律**：
   - 若有候选取得三档两轮正反方向一致净胜，晋升为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v32.dll`（不覆盖本机 5 处生产部署与 v0.3.0 ZIP），并将分支 3 的 `n` 重置为 `0`；若无全档稳定净胜，如实记录负结果并将分支 3 的连续未晋升计数更新为 `n = 2 / 3`。
   - 完整数据与分析写入 `Development/ptx-patcher/v32/README.md`，同步更新 `DevHistory.md` 与 `WorkingPlan.md`，**清理所有临时大二进制（`.rgb32`, `.cubin`, `.ptx`, 临时候选 DLL），立即执行 `git commit`（严禁加 `Co-Authored-By`），不 push**。

### V3.2 执行回执（2026-10-31，闇）

11个计时单因素/组合均未通过三档两轮正反全胜门槛，不晋升V3.2 DLL，保留V3.1_pack5；分支3保持Open、n=2/3，分支4保持Open、n=0/3。完整证据见[回执](ptx-patcher/v32/README.md)、[计时](ptx-patcher/v32/timing-summary.md)、[四表](ptx-patcher/v32/hardware-baseline.md)、[验收](ptx-patcher/v32/validation.json)。

完成Phase-Split、UP单因素、split+UP、等价shift及组合，以及六个单核cap控制。pool162regs/零STACK/3CTA确实跨阶；其他核跨阶引入8～152B STACK，均按真实整帧ABBA裁决。有效正式配对288次，初轮并发72次全部排除并串行补齐；成功严格运行合计363次末帧0bit/maxabs0/nonfinite0，7类别名GPU、UP/shift各33554432对原语、13项回归通过。repeat结果详见回执。

新2×2另48次：去Decode为0.563500/0.992000/1.429500ms，去Pack为0.145500/0.102500/0.167250ms，二者均12/12正。**新事实：Pack重新呈全档正敏感度，分支2的Closed是阶段状态，不是见底证明；交主脑复核重开/排期。** 分支4仍Open，本轮未实现，分支3未达K=3仍Open。保护性SHA前后不变；清理临时大产物，立即独立commit，不部署、不push，无Co-Authored-By。

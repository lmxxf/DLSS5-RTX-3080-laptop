# WorkingPlan — PTX V2.4 极限攻坚任务单与实测回执（2026-10-27）

> **本轮已完成**：推荐V2.4仅启用C（mask8）；A/B与D完成隔离/组合和负结果验证，未进默认。原20:15任务单保留如下，最终回执见第3节。主fast仍为V2.3，本轮不部署、不push。

## 0. 当前基线
- 唯一基线：**`PTX V2.3`**（commit `f786183`，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v23.dll`，SHA256 `b9c463beec6aba945beb2ce31aa96edd52fbae2933cb72cdb6f394b52bda9ca6`）
  - 720p (`1280×720`)：**`6.13 ms`**
  - 900p (`1600×900`)：**`8.93 ms`**
  - 1080p (`1920×1080`)：**`11.68 ms`**
- 已有工具：`Development/ptx-patcher/v23/build_profile.py` 与 `run_profile.py`（NVAPI `LaunchCuKernelChain` 82 次发射逐 FB / 逐 Kernel 计时器）+ 未插桩 `bench_sky.exe` 配对正反 ABBA。

---

## 1. 主脑代码审计发现的四大实锤优化靶子（请逐项实现与隔离/组合消融）

### 靶子 A：全网 `4,744` 处 `FP8_UP`（`cvt.rn.f16x2.e4m3x2`）同步升级 `prmt 0x9180` 5 指令解包
- **现状**：`V2.3` 只把 `mma` 内部的 `even_odd_decode_lines` 换成了 `0xa280 / 0xb391` 的 4 指令解包，但遗漏了 `build_sm86_dlls.py` 第 81-90 行的 `fast_fp8_pair_to_half_lines(source, destination)`！全网 `FB00~06` 仍有 **`4,744` 处 `FP8_UP`**（`FB00` 584、`FB01` 832、`FB02` 832、`FB03` 832、`FB04` 704、`FB05` 704、`FB06` 256）在使用旧的 7 条指令版本（`prmt 0x1404` + `and 0x80008000` + `and 0x7f007f00` + `shr 1` + `or` + `mov 0x5c005c00` + `mul.rn.f16x2`）。
- **改法**：将 `fast_fp8_pair_to_half_lines(source, destination)` 升级为同款字节符号复制 `prmt`：
  ```ptx
  prmt.b32 {destination}, {source}, {source}, 0x9180;
  and.b32 {destination}, {destination}, 0x017f017f;
  shl.b32 {destination}, {destination}, 7;
  mov.b32 dlssnr_fp8_scale, 0x5c005c00;
  mul.rn.f16x2 {destination}, {destination}, dlssnr_fp8_scale;
  ```
  - 穷举全部 `65,536` 个 `uint16` 输入验证与旧版 100% 严格 `0 bit-diff`；
  - 每次调用从 7 条指令降为 5 条（全网立省 **`9,488` 条静态指令**），且不再需要 `dlssnr_fp8_sign` 和 `dlssnr_fp8_abs` 两个临时寄存器！

### 靶子 B：`SWAR` `FP8_DOWN`（全网 `8,944` 处 `cvt.rn.satfinite.e4m3x2.f16x2`）常数合并 + 成对融合打包（Fused Quad-Pack）
1. **单条 `pack` 内部常数合并（21 条 → 20 条，已穷举 `0..0x5f00` 验证 0 进位、100% 0 bit-diff）**：
   - 在 `v22/codegen.py` 第 18-21 行：
     ```ptx
     add.u32 dlssnr_v22_n, dlssnr_v22_a, 0x003f003f;
     add.u32 dlssnr_v22_n, dlssnr_v22_n, dlssnr_v22_t;
     shr.u32 dlssnr_v22_n, dlssnr_v22_n, 7;
     add.u32 dlssnr_v22_n, dlssnr_v22_n, 0x00c000c0;
     ```
     因为 `0x00c0 << 7 = 0x6000`，且 `dlssnr_v22_a` 已通过 `min.f16x2` 钳位在 `<= 0x5f00`，低 16 位最大和为 `0x5f00 + 0x603f + 1 = 0xbf40 < 0x10000`（**绝对不会向 bit 16 进位污染高 16 位**）！
     因此可直接合并为：
     ```ptx
     add.u32 dlssnr_v22_n, dlssnr_v22_a, 0x603f603f;
     add.u32 dlssnr_v22_n, dlssnr_v22_n, dlssnr_v22_t;
     shr.u32 dlssnr_v22_n, dlssnr_v22_n, 7;
     ```
     当场砍掉 `add.u32 ..., 0x00c000c0;`（全网 `8,944` 处立省 `8,944` 条指令）！
2. **检查并融合残留的成对打包 `cvt %rs0, %r_lo; cvt %rs1, %r_hi; mov.b32 %r_dst, {%rs0, %rs1};`（Fused Quad-Pack）**：
   - 在 `lower_fp8_mma` 之后，全网仍残留 **`7,540` 处 `FP8_PACK`** 和 **`8,944` 处 `FP8_DOWN`**。其中绝大多数是连续两条 `cvt.rn.satfinite.e4m3x2.f16x2 %rs0, %r_lo; cvt.rn.satfinite.e4m3x2.f16x2 %rs1, %r_hi;` 紧接着一条 `mov.b32 %r_dst, {%rs0, %rs1};`（且 `%rs0, %rs1` 不再被其他指令使用）！
   - 目前做法：第一条 `cvt` 算完字节 0/2 后做 `prmt 0x4420` + `cvt.u16.u32 %rs0`，第二条 `cvt` 又重新 `mov` 一遍常量（`0x5f005f00`, `0x40004000`, `0x24002400`）算完字节 0/2 后做 `prmt 0x4420` + `cvt.u16.u32 %rs1`，最后再 `mov.b32 %r_dst, {%rs0, %rs1}`。
   - **Fused Quad-Pack 改法**：对同一基本块内且 `%rs0, %rs1` 仅被该 `mov.b32 %r_dst, {%rs0, %rs1}` 消费的三联体，在一个块内**只加载一次常量寄存器**，算出 `n_lo`（有效字节在 byte 0, 2）和 `n_hi`（有效字节在 byte 0, 2），最后直接用 **一条 `prmt.b32 %r_dst, n_lo, n_hi, 0x6420;`** 拼出 `%r_dst`！
   - 每对立省：3 条重复常量 `mov.b32` + 2 条 `prmt 0x4420` + 2 条 `cvt.u16.u32` + 1 条 `mov.b32 {%rs0, %rs1}` - 1 条 `prmt 0x6420` = **每对净省 7 条指令**！

### 靶子 C：`fast_render_fp8_mma_run` 按需即时交错解包 + 死亡操作数寄存器池复用（JIT Interleaved Decode + Dead-Operand Register Pool Recycling）
- **现状问题**：`fast_render_fp8_mma_run` 先在一个大循环里把整个 `run`（在 `FB04/05` 长达 64 条 `mma`）的所有操作数一次性解包到 `dlssnr_fp16_0_0 ... dlssnr_fp16_N_1`，再发射所有 `mma`。
  - 在 `FB05` 的 64-mma run 中，`A` 的 4 个 tile（`%r363..370`, `%r387..394`, ...）其实是严格分段在 `mma[0..15]`, `mma[16..31]`, `mma[32..47]`, `mma[48..63]` 中使用的，却在开头同时占用了 64 个临时寄存器！
- **改法**：
  - 预计算该 `run` 中每个操作数 `r` 的 `last_use[r] = max(i for i, m in enumerate(matches) if r in m_operands)`；
  - 遍历 `for i, m in enumerate(matches):`：
    - 若 `m` 的某个操作数 `r` 尚未解包，从 `free_pairs` 空闲池取出（或新分配）一对临时寄存器 `(first, second)`，**紧贴在该条 `mma` 之前发出 `r` 的解包指令**（使解包 ALU 指令与 `mma` 指令在流水中天然交错）；
    - 发出该条 `m` 的两条 `m16n8k16` 指令；
    - 对 `m` 中满足 `last_use[r] == i` 的操作数 `r`，立即将其 `(first, second)` 归还到 `free_pairs` 供后续操作数复用！
- **预期收益**：
  - 数值结果 100% 严格 `0 bit-diff`，解包指令总数完全不变；
  - 每个 `mma_run` 声明的临时寄存器峰值暴降：`FB00` `64->40` (-37.5%)、`FB01/02` `80->56` (-30%)、`FB03` `96->56` (-41.7%)、`FB04` `160->112` (-30%)、`FB05` `128->80` (-37.5%)、`FB06` `144->20` (-86.1%)！
  - 请用 SASS 审计与实机计时验证该因子对 `STACK` spill 和帧耗时的独立及组合影响（若某 FB 因 `ptxas` 调度喜欢 upfront 则可按实测取舍）。

### 靶子 D：基于新代码寄存器占用与 `STACK` spill 的 Per-Fatbin `.maxnreg` 精细重标定
- 在应用上述指令精简与寄存器池复用后，审计 `FB00~FB06` 的 `STACK` spill 和每核寄存器数：
  1. **`FB01 (C64)` 与 `FB02 (C128)`**：在 `V2.3` 中 `FB01` 仍锁在 `.maxnreg 168`，导致 `STACK` spill 涨到了 `192 B`（518 条 `LDL+STL`），而 `FB01` 每个 CTA 仅 64 线程（2 Warp），放宽 `.maxnreg` 到 `192 / 224 / 255` 不会降低受 Shared Memory 限制的 CTA 驻留数，却能彻底清零 `FB01` 的 spill！请实测 `FB01`（及 `FB02`）放宽 `.maxnreg` 的净收益。
  2. **`FB04 (C512)` 与 `FB05 (ViT)`**：在寄存器压力大幅下降后，测试 `FB04` / `FB05` 在不同 `.maxnreg` 台阶（如 `168 / 192 / 224 / 255`）下的逐 FB 耗时与全网帧耗时。

---

## 2. 验收与交付纪律
1. 所有算术/解包/打包改写必须通过穷举单元测试 + 实机帧输出相对 `V2.3` **严格 `0 bit-diff`（`max_abs = 0`, `PSNR = ∞`）**。
2. 对各个因子（靶子 A / B / C / D）做好清晰的消融与组合验证，只保留带来真实净提速的组合，产出推荐版 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll`（保持 `266,414,592 B` 原槽位 15/15 `O4`）。
3. 使用未插桩 `bench_sky.exe` 在 720p / 900p / 1080p 三档完成 50 warmup / 80 iter 正反 ABBA/BAAB 配对评测，并附上 `v24/README.md` 报告。
4. 更新 `Development/DevHistory.md` 与 `Development/WorkingPlan.md`，清理临时大二进制，立即 `git commit`（严禁加 `Co-Authored-By`），不 push。


---

## 3. 执行回执：V2.4选C，不把PTX瘦身预期当作实际收益

- **推荐产物**：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll`，266,414,592B、15/15 O4原槽位，SHA256 `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`。全15重编与实测候选SHA及PTX完全一致。入口 `python3 Development/ptx-patcher/v24/build_recommended.py`，mask8，沿用SWAR/PRMT8/multidef_nq/原hot255。
- **严格验收**：A16,777,216组GPU穷举u16＋高位干扰0bit；B bias/quad各33,554,432组覆盖全half位型、两位置、非有限与干扰位0bit。C两个128warps/64-MMA长run对照（含mapped累加器别名先覆写的风险）0bit；18快验＋120因素＋96cap＋24条件组合=258次末帧0bit/maxabs0/PSNR∞/nonfinite0，另16次50/20 NVAPI逐FB诊断末帧0bit。既有10项回归通过。
- **正式三档50/80正反ABBA/BAAB**，配对V2.3→C：**6.24900→6.20100 / 9.12850→9.09175 / 12.20700→12.02650ms**，耗时下降 **0.768%/0.403%/1.479%**；两方向都赢。1080p GPU min均值11.72350→11.72300ms，基本不变。默认DVFS；不与历史6.13/8.93/11.68ms跨轮硬比。[完整表](ptx-patcher/v24/results.md)
- **A/B未入默认**：A实现7→5条UP，bias实码20→19条（非任务单口径21→20），但bias在40活跃核SASS总条数未变。7,540个泛型拼接匹配不等于同等数量合格quad；同BB、单def/单消费者筛选只融合 **1,688对**（FB01 456、FB02/03各616）。ABC相对V2.3也赢，但直接ABC对C的900/1080收益方向变号，AB增量不稳定；不把C收益归给AB。实现留作显式开关实验。
- **C保留**：声明峰值64→40、80→56、80→56、96→56、160→112、128→80、144→20，解包/MMA顺序及run入口读值语义保持；遇到源或mapped别名先被MMA覆写时提前保存。物理spill未全消失：全导出FB01 STACK192→224B、LDL+STL477→507；FB04 96→88B、125→127；FB05仍16B。虚拟声明减少不是零spill保证。
- **D实测纠正前提**：C64活跃Shared4096B；CUDA occupancy API的理论最大驻留是168cap下12warps/SM、192/224/255下8，不是“占用率不掉”。255清零活跃spill但整帧慢0.759%；FB04 cap168慢6.723%、FB05 cap168慢4.219%，其他微小或变号收益不稳定，原caps保留。[逐FB时间戳](ptx-patcher/v24/profile-results.md)、[资源/理论occupancy](ptx-patcher/v24/caps-resources.json)。这些API/时间戳不是动态stall计数器。
- **工程收尾**：[回执](ptx-patcher/v24/README.md)、[验收](ptx-patcher/v24/validation.json)、[清理](ptx-patcher/v24/cleanup.json)。保留用户原任务单并追加实测结果。清理临时大DLL/cubin/PTX/RGB，保留推荐DLL与文本证据；主fast及V2.3副本仍为b9c463be…，三个正式ZIP保护性SHA未变。不部署、不push，立即独立commit，无Co-Authored-By。

# WorkingPlan — PTX V2.5 攻坚任务与负结果回执（2026-10-27）

> **已完成**：Hybrid全网及FB00-only均未获得稳定净收益，推荐仍为V2.4；未命中“更快才生成正式V2.5 DLL”的条件。新增三档实测MMA/循环计数器与循环修正账本，见第4节。原21:20任务单保留，不部署、不push。

## 0. 当前基线
- 唯一基线：**`PTX V2.4`**（commit `9e4d2db`，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll`，SHA256 `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`）

---

## 1. 算力缺口根因定位：`PRMT` 字节置换管道拥堵（`T_prmt = 2.104 ms` in FB00）
主脑将 `v23/profile.json`（82 次真实发射的 Grid×Block）与 `v24/sass-audit.json`（40 个活跃 Kernel 的精确 SASS 计数）联立，算出了 1080p (`1605 MHz`, `77.04M SM-cycles/ms`) 下各硬件执行管道的真实理论负载：
- 在第一大模块 **`FB00 (C32)`（1080p 实测 `4.041 ms`）** 中：
  - `T_hmma (Tensor Core, 4.0 SM-cyc/inst)` = **`2.940 ms`**
  - **`T_prmt (PRMT 置换单元, 2.0 SM-cyc/inst)` = `2.104 ms`（！！）**
  - `T_int/shf (LOP3/IADD3/SHF, 0.5 SM-cyc/inst)` = **`1.150 ms`**
  - `T_fp16 (HMUL2/HFMA2, 0.5 SM-cyc/inst)` = **`1.147 ms`**
  - `T_mem` = `0.137 ms`
- **关键发现**：在 `sm_86` 上，`PRMT` 每个 Sub-partition 每周期只有 4 通道（全 SM `0.5` warp-inst/clk，即 **2.0 SM-cycles/条**，吞吐仅为 `LOP3 / IADD3 / HMUL2` 的 **1/4**）！而在 `V2.3/V2.4` 中，`PRMT8` 解包对偶半边（`0xa280`）和奇半边（`0xb391`）均使用了 `PRMT`，导致 `pre_block` 单核静态 `PRMT` 高达 **732 条**（超过 `HMMA` 的 528 条），将低速 `PRMT` 管道塞爆至 `2.104 ms`！

---

## 2. `PTX V2.5` 攻坚靶子

### 靶子 1：偶 `PRMT` + 奇 `LOP3` 异构分流 8 指令解包（Hybrid `PRMT + LOP3` 8-Inst Decode）
- **数学原理（主脑已穷举全部 65,536 种 `(byte1, byte3)` 组合 + 任意 `byte0/2` 噪声验证 100% 严格 `0 bit-diff`）**：
  - **偶半边（`first`，byte 0 at `0..7`, byte 2 at `16..23`）**：保持 4 条指令（用 1 条 `PRMT`）：
    ```ptx
    prmt.b32 {first}, {register}, {register}, 0xa280;
    and.b32 {first}, {first}, 0x017f017f;
    shl.b32 {first}, {first}, 7;
    mul.rn.f16x2 {first}, {first}, dlssnr_fp8_scale;
    ```
  - **奇半边（`second`，byte 1 at `8..15`, byte 3 at `24..31`）**：符号位 bit 15 和 bit 31 **本来就已经在 FP16x2 的符号位（`0x80008000`）上**！完全不需要 `PRMT`，直接用 **4 条指令（0 条 `PRMT`、0 个额外临时寄存器）** 走 4 倍吞吐的 `LOP3` 管道：
    ```ptx
    and.b32 {second}, {register}, 0x7f007f00;
    shr.u32 {second}, {second}, 1;
    lop3.b32 {second}, {register}, {second}, 0x80008000, 0xca;
    mul.rn.f16x2 {second}, {second}, dlssnr_fp8_scale;
    ```
    *（注：`lop3.b32 d, a, b, c, 0xca` 当 `a=register, b=second, c=0x80008000` 时，真值表 `(a & c) | (b & ~c) = (0xf0 & 0xaa) | (0xcc & 0x55) = 0xa0 | 0x44 = 0xe4` 或當 `a=register, b=0x80008000, c=second` 时为 `(a & b) | c = (0xf0 & 0xcc) | 0xaa = 0xc0 | 0xaa = 0xea`！请特别注意：**因为 `second` 在 `(register & 0x7f007f00) >> 1` 之后，其 bit 15 和 bit 31 恒为 0**，所以根本不需要 `& ~0x80008000`，直接计算 `(register & 0x80008000) | second` 即可！用 `lop3.b32 {second}, {register}, 0x80008000, {second}, 0xea;`（即 `(a & b) | c`）一步到位！）*
- **核心优势**：
  - 总指令数依然是 **8 条**（4 + 4），**0 个额外临时寄存器**（无需 `dlssnr_fp8_abs / sign`），**100% 严格 `0 bit-diff`**！
  - 将全网所有非 mapped `mma` 解包的 `PRMT` 数量**直接砍半（`-50%`）**，一半走 `PRMT` 单元、一半走 `LOP3` 单元，实现硬件子分区内部 `PRMT` 与 `INT32/LOP3` 管道的完美负载均衡！

### 靶子 2：排查 `mapped` 操作数的 `prmt 0x5410 / 0x7632` 与 `FB04 / FB05` 循环体内动态瓶颈
1. 检查 `V2.5`（启用靶子 1 + `V2.4` 的按需解包寄存器池 `C`）编译后的 SASS 指令变化：确认 `PRMT` 和 `IMAD.SHL.U32` 是否显著下降，并测量对 `V2.4` 的三档正反 ABBA 净收益。
2. 同时检查 `FB05 (ViT)` 和 `FB04 (C512)`（占 1080p `3.90 ms`、720p `2.63 ms`，含 `2,134` / `1,026` 条 `BRA` 分支）：
   - 导出并检查 `cc_vit_1d_ffn_expand_chained_fp8` / `contract` / `qkv` 的循环结构，算清其循环迭代次数 `K_iters`，把 `FB04 / FB05` 的真实动态 `HMMA` 与动态辅助指令数补进 `v25/README.md` 的动态 Roofline 账本中，消除静态计数遗漏循环圈数的盲区！

---

## 3. 验收与交付纪律
1. 穷举测试验证 Hybrid `PRMT + LOP3` 解包（`0xea` LUT）与 `V2.4` 100% 严格 `0 bit-diff`。
2. 在未插桩 `bench_sky.exe` 上完成 720p / 900p / 1080p 三档 50 warmup / 80 iter 正反 ABBA/BAAB 配对实测。
3. 若净耗时优于 `V2.4`，产出 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v25.dll` 与 `v25/README.md`，更新 `DevHistory.md` 与 `WorkingPlan.md`，清理临时大二进制，立即 `git commit`（无 `Co-Authored-By`），不 push。


---

## 4. 实测回执：分流正确但不提速，保留V2.4

- **Hybrid8已实现、仅作可选实验**：奇半边使用`and/shr/lop3 0xea/mul`，偶半边保留PRMT，V2.4寄存器池/mapped/SWAR/cap不变。33,554,432组GPU对照（两parity完整字节对与干扰位、含非有限）0bit。15/15原槽位O4、266414592B。[实现/报告](ptx-patcher/v25/README.md)
- **全网50/80正反ABBA/BAAB**，配对V2.4→Hybrid：720 **6.17950→6.20500**、900 **8.93025→9.04750**、1080 **11.72275→11.96775ms**，耗时增0.413%/1.313%/2.090%，每档两方向均慢。FB00-only另16次：720约快0.207%，1080约快0.019%但方向变号、min变慢，无稳定收益。6快验＋40正式共46次末帧0bit/maxabs0/PSNR∞/nonfinite0，10项既有回归通过。[配对表](ptx-patcher/v25/results.md)
- **SASS核验**：40活跃核PRMT25483→19774、IMAD.SHL12169→6456、LOP3 32370→38081、SHF.R6355→12067，总静态183651→183800。pre_block PRMT732→629，post828→716，**非mapped模板减半不等于全网减半**。FB01 STACK224→200B但LDL+STL507→529；没有由较少PRMT断言完美均衡/净收益。
- **新增实际计数器**：独立诊断DLL为FB00/04/05追加UAV指针，专用NVAPI runner每帧清零/readback；收敛MMA run的lane0原子计数，FP8 K32按2条HMMA.16816等价操作、原生FP16 K16按1条计，并测自然计算循环入口、decoder PTX操作及mapped/unmapped事件。三档1/1诊断末帧与未插桩V2.4严格0bit，82次Grid/Block序列与50帧参数捕获一致；另三对50/1参数捕获/参考也0bit。诊断耗时不用于速度比较。
- **K圈数确认**：ViT expand16；contract15＋1尾段；QKV15＋1；projection7＋1；attention为ceil(tokens/64)=5/7/10，实际token参数288/448/640。C512两个ffwd循环7、8，多个projection/final_head8，qkv及proj_pool7圈＋循环外计算。不是把整核静态数统一乘16。[逐核计数与模型](ptx-patcher/v25/dynamic-ledger.md)
- **实测HMMA语义等价次数**：720 FB04/05为4,694,016/20,185,088；900为7,155,712/27,000,832；1080为9,699,328/35,389,440。其循环修正辅助SASS模型分别33,309,600/162,130,944、50,889,440/216,246,272、69,783,168/286,136,320。模型HMMA逐核严格匹配计数，但辅助列未测谓词/分歧、helper与重试，**不是精确硬件issued计数或任意重试上界**。频率/管道吞吐仍为成本模型输入，非本轮测出的独占吞吐。
- **FB00 mapped占大头**：1080实测MMA解包unmapped pair12,892,128、mapped pair30,109,220；仅减unmapped半边，decoder PTX PRMT总事件仅约减14.99%。PTX事件会被编译器折叠，不直接套SASS吞吐算周期。2.104ms静态模型值不足以单独证明PRMT在关键路径。
- **交付**：保留V2.4推荐SHA `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`，不生成正式v25.dll。失败候选和诊断DLL只留重建源码/SHA，临时大文件清理。[验收](ptx-patcher/v25/validation.json)、[清理](ptx-patcher/v25/cleanup.json)。主fast/V2.4及三ZIP收尾哈希不变；更新文档后立即独立commit，无Co-Authored-By，不部署、不push。

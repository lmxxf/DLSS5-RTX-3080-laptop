# WorkingPlan — PTX V2.6 Low/High攻坚任务与实测回执（2026-10-28）

> **已完成并推荐V2.6**：三档同轮耗时下降1.96%/2.27%/2.30%；相对V2.4的PSNR为61.82/61.77/58.42dB，存在FP16舍入差，非0bit升级。原01:18任务单保留，实测结果见第3节。本轮不部署、不push。

## 0. 当前基线
- 唯一基线：**`PTX V2.4`**（commit `9e4d2db` / `6dccbdc`，`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll`，SHA256 `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`）

---

## 1. 重大突破发现：从“偶奇拆解 (`{0,2}` / `{1,3}`)”切换为“低高半字拆解 (`{0,1}` / `{2,3}` Low/High Split)”！

在 `V2.5` 的运行时插桩数据中，我们发现了一个极其关键的结构事实：
- 在 `FB00`（1080p）的 `4,300 万` 个 MMA 解包对中，**非 `mapped`（FP8 编码输入）仅占 `29.98%`（`12,892,128` 对），而 `mapped`（由原生 `f16x2` 寄存器 `low, high` 经 `cvt`+`mov.b32 {rs0, rs1}` 打包的激活特征）占了整整 `70.02%`（`30,109,220` 对）**！
- **为什么在 `V2.0 ~ V2.4` 中，这 `70.02%` 的 `mapped` 操作数每一个都要执行两条 `prmt.b32`（`0x5410` 和 `0x7632`）并占用 2 个 `.b32` 临时寄存器？**
  - 因为 `V2.0` 当时还没有发明 `PRMT8` 解包，为了迁就 `30%` 的非 `mapped` 操作数做 `0x007f007f / 0x7f007f00` 偶奇位掩码，选择了按 **偶下标 `{byte0, byte2}`** 和 **奇下标 `{byte1, byte3}`** 拆解 `m16n8k32`！
  - 这导致原本已经是 `f16x2` 格式的 `low = {h0, h1}`（对应 `{byte0, byte1}`）和 `high = {h2, h3}`（对应 `{byte2, byte3}`）被迫每次都要执行：
    ```ptx
    prmt.b32 first, low, high, 0x5410;   // 取 {h0, h2}
    prmt.b32 second, low, high, 0x7632;  // 取 {h1, h3}
    ```
- **核心数学洞察**：
  - 在 `V2.3` 升级为 `PRMT8` 解包之后，非 `mapped` 操作数本身就已经改用两条 `prmt.b32`（`0xa280` 和 `0xb391`）选字节了！
  - 既然非 `mapped` 操作数用任意字节选择器都是完全相同的 8 条指令，如果我们把线程内的 4 个 K 元素从 **“偶奇拆解 `{0, 2}` + `{1, 3}`”** 改为 **“低高半字拆解（Low/High Split）：`first = {0, 1}` + `second = {2, 3}`”**：
    1. **对于占 `70%` 的 `mapped` 操作数（当不启用 `--quantize-mapped` 时）**：
       - `first`（元素 `{0, 1}`）**直接就是原生的 `low` 寄存器本身**！
       - `second`（元素 `{2, 3}`）**直接就是原生的 `high` 寄存器本身**！
       - **完全不需要 `prmt 0x5410` 和 `prmt 0x7632`（0 条解包指令！），也完全不需要为 `mapped` 操作数分配任何 `dlssnr_fp16_*` 临时寄存器（0 个临时寄存器！直接将 `(low, high)` 原生寄存器名填入两条 `mma.sync.aligned.m16n8k16` 的操作数槽位中）**！
       - *（特别注意别名保护：若某个 `mapped` 操作数 `r` 的底层源寄存器 `low` 或 `high` 在同一个 `mma_run` 内会被更早的一条 `mma` 的输出累加器 `d0, d1` 覆写，则仅对该被覆写的 `low`/`high` 在覆写前用 1 条 `mov.b32 tmp, low/high` 备份即可；未被覆写的直接零拷贝直通 `low, high`！）*
    2. **对于占 `30%` 的非 `mapped`（FP8 编码）操作数**：
       - 只需将 `v23/decode.py` 中的选择器从偶奇 `0xa280 / 0xb391` 改为低高半字 **`0x9180`（取 `byte0, sign0, byte1, sign1`）** 和 **`0xb3a2`（取 `byte2, sign2, byte3, sign3`）**：
         ```ptx
         prmt.b32 {first}, {register}, {register}, 0x9180;
         and.b32 {first}, {first}, 0x017f017f;
         shl.b32 {first}, {first}, 7;
         mul.rn.f16x2 {first}, {first}, dlssnr_fp8_scale;
         prmt.b32 {second}, {register}, {register}, 0xb3a2;
         and.b32 {second}, {second}, 0x017f017f;
         shl.b32 {second}, {second}, 7;
         mul.rn.f16x2 {second}, {second}, dlssnr_fp8_scale;
         ```
       - 非 `mapped` 操作数依然是 **8 条指令**，0 额外开销！
       - *（注：甚至在 `second` 的 `0xb3a2` 中，`byte3` 原本就在 `register` 的最高字节 `bit 24..31`，其符号位已在 `bit 31`，不过先用对称的双 `PRMT` `0x9180 / 0xb3a2` 保持与 `V2.4` 完全同构的指令类型！）*

---

## 2. 预期效果与验证要求
1. **指令与寄存器双重暴降**：
   - 全网所有 `mapped` 操作数的 `prmt 0x5410 / 0x7632` **100% 消失**（仅 `FB00` 1080p 一帧即消除 **`6,021.8 万` 次动态 PTX `PRMT` 事件**，全网静态 `PRMT` 预计减少上万条）！
   - `mapped` 操作数不再占用 `dlssnr_fp16_*` 临时寄存器池（除非其 `low/high` 源寄存器在同 run 内被更早的 `d0/d1` 覆写），进一步压低全网寄存器压力与 `STACK` spill！
2. **精度与画质验证**：
   - 注意：因为每条 `m16n8k32` 内部从 `({k0,k2} + {k1,k3})` 变成了 `({k0,k1} + {k2,k3})`（与原版 Ada/Blackwell 的低 16 / 高 16 累加次序更接近！），FP16 加法结合顺序改变会产生正常末位 ULP 舍入差异（如同 `V1 → V2.0` 时一样）。
   - 请验证：
     ① 单算子测试：当输入精确可表示（无 FP16 累加舍入差）时，`lowhigh` 拆解与 `evenodd` 拆解 100% 数学恒等；在随机 FP8/FP16 输入下，相对 FP32 金标准的误差分布与 `evenodd` 完全同级；
     ② 整网三档输出：相对 `V2.4`（及 `V1`）的 PSNR 保持在 **`~58 ~ 63 dB`（天空 0 变号、0 NaN/Inf）** 的完全同等无损精度水平！
3. **性能实测与 `.maxnreg` 复核**：
   - 使用未插桩 `bench_sky.exe` 在 720p / 900p / 1080p 三档完成 50 warmup / 80 iter 正反 ABBA/BAAB 配对实测；
   - 审计 40 个活跃 Kernel 的静态 SASS 指令数（特别是 `PRMT` 与总指令数减少量）以及各 FB 的 `STACK` spill 变化（看 `FB01` / `FB04` / `FB05` 的 spill 是否随之大幅下降甚至清零！）；
   - 若取得显著净提速，产出 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v26.dll` 与 `v26/README.md`，更新 `DevHistory.md` 与 `WorkingPlan.md`，清理临时文件后立即 `git commit`（无 `Co-Authored-By`），不 push。


---

## 3. V2.6执行回执

- **推荐产物**：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v26.dll`，266414592B（254.07MiB）、15/15 O4原槽位，无扩节。SHA256 `04b01f0c963061e24d1fd34f5097043d4eeddb001c846d9002e4e2bdc73ad788`，全15重建与实测候选SHA/PTX相同。`python3 Development/ptx-patcher/v26/build_recommended.py`复现。
- **映射证明与保护**：线程内low/high对应原K=`2*j-(j&1)+2*phase`，两相覆盖0..31且A/B一致；不是全局连续的前后16个K，未证明更接近原生sm120内部顺序。mapped直接引用low/high，只对首次覆写早于最后读取的底层源备份，精确到半条MMA，覆盖第一K16覆写第二K16所读high。真实全网mapped备份mov为0，假设边界由GPU用例验证。
- **原语**：768标量槽坐标证明；33,554,432组解码重排对照0bit；全部64种mapped/encoded分配×16组整数矩阵，两版均精确等于CPU积＋0.5；5类128warp别名/长run测试对独立LowHigh入口快照参考全0bit，包括全mapped无覆写0临时/0PRMT。随机FP8、混合FP16/FP8、全mapped FP16各256组，对FP32-rounded高精度参考RMSE比值约1.001/1.024/0.998，误差同量级，不作逐点误差不增承诺。
- **正式50/80正反ABBA/BAAB**：配对V2.4→V2.6 median均值 **6.09950→5.98000 / 8.92475→8.72200 / 11.73225→11.46250ms**，耗时降1.959%/2.272%/2.299%，各档两方向均胜出；min均值6.02800→5.91325、8.71250→8.52300、11.49050→11.22550。默认DVFS，不跨轮套旧基准。[完整表](ptx-patcher/v26/results.md)
- **质量与重复性**：正式三档相对V2.4 PSNR **61.819121/61.767286/58.421047dB**，maxabs0.0048828125/0.005615234375/0.009765625；相对V1为 **62.124349/61.854969/60.884550dB**，maxabs0.00439453125/0.006103515625/0.00732421875。9初验＋24配对计时＋6V1参考共39次末帧全部finite；同版本同配置重复全0bit，跨版本有舍入差。天空变号0、V2.6正式HF RMS0.000102746766。PSNR是到移植基线的距离，不是原生新卡/全网FP32绝对画质gold。
- **编译资源**：40活跃核静态PRMT25483→19864（-5619），总SASS183651→178170（-5481），HMMA13188不变；所有导出生成路径去掉21712条mapped PTX PRMT。FB00临时池声明峰值40→24，其他FB最大池仍受非mapped控制。活跃C32 prefix REG234→196、inpview234→200、ds231→199、outview236→197、up229→212。全导出FB01最大STACK224→104B、LDL+STL507→381；活跃outview224→96，ds/inpview80→64，但up88→96回退。FB04/05最大STACK仍88/16B。保留hot255，未声称零spill或全局最优。
- **交付纪律**：[回执](ptx-patcher/v26/README.md)、[原语](ptx-patcher/v26/primitives.json)、[别名测试](ptx-patcher/v26/alias-tests.json)、[验收](ptx-patcher/v26/validation.json)。10项既有回归通过；清理重复DLL/PTX/cubin/RGB，保留推荐DLL和文本证据；主fast、V2.4、V1备份与三ZIP收尾哈希未变。不部署、不push，阶段独立commit，无Co-Authored-By。

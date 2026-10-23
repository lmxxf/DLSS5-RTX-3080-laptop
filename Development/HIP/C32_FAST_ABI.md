# Production C32 FAST3 FFN candidate

独立 `c32_fast.hip`，复用 tiled LDS 装载，但采用生产 FAST3 的舍入日程；不替换 `c32_reference` / `c32_tiled` / `c32_wmma` 的逐值参考实现。

已审原文件 `native_c32_ffn_fused.hlsli::ffn_fused/ffn_activate`，并和 `native_wave_c32_ffn_blocked.hlsl` 的 `NATIVE_C32_FFN_FAST3` 分支核对：

- expand：输入饱和转换为 E4M3，K32 FP32 dot 直接进 clamp/polynomial，没有中间 H；poly 中 q、p 禁用 FMA contraction，末尾一次 E4M3 量化。
- 普通残差路径：被 SAT8 裁到 ±448 的输入乘 f32 scale，不先 H；依次四个 K32 矩阵累加，最后仅一次 H。HIP 将每个 K32 拆成两个 K16 WMMA，并让前一 acc 作 C seed，不采用 exact 路径的每组 H(acc+sum)。是否与 D3D K32 指令的内部 C 相加次序完全一致由实测判断。
- **map_mode=3 是另一条残差路径**：F(input) 乘三份 E4M3 分解的对角矩阵，三次 K32 MMA 后才进入四组 contract；不能用普通 input×scale 代替。map3 由新增独立导出处理（见下），原 map0 ABI 不变。也不包含 RGB/noise prefix 或 post merge 的输入准备。

外部激活/权重仍为 f32，weights 为原 8736 元素布局。矩阵权重必须已在有限 FP8 格点；残差 scale 保留 f32。输入是已完成上游映射的 tile-major H()-rounded 特征，布局 `[tokens][32]`。

| kernel | 参数 | grid.x | block.x |
|---|---|---:|---:|
| c32_ffn_expand_fast | input, fw, hidden, tokens | ceil(tokens/64)×2 | 512 |
| c32_ffn_contract_fast | input, hidden, fw, output, tokens, raw_output | ceil(tokens/64) | 256 |

hidden 为 `[tokens][128]` 的 f32（承载 FP8 格点），output 为 `[tokens][32]` 的 f32（最终 H 后）；raw_output=1 保留 H 结果，0 额外做 F。

## 真生产 HLSL 对照

`build_c32_fast_oracle.ps1` 编译原 `native_wave_c32_ffn_blocked.hlsl`，没有重写 HLSL 数学：FAST2/FP8/FAST3/PRECISE_CHAIN/SAT_CAST 均 1，HALF_STREAM/TILED_WEIGHTS/MAPPED_INPUT 均 0，以 map0 与 f32 输出暴露相同 FFN 算法。参考 kernel 实际使用 production FP8 矩阵及最终 H，不用原 scalar C32 作为这一日程的裁判。

```text
c32_fast_ffn_validate.exe ASSETS_DIR c32_fast.hsaco c32_fast_oracle.cso OUTPUT_PREFIX
```

测试 16×16 工作网格，E4M3、half、超 ±448 饱和边界三类输入；host 按生产字节偏移打包真 block1 权重，比较最终 FFN 的 bitdiff/numericdiff/invalid/maxabs，保存 HLSL/HIP 输出及 HIP hidden。hidden 尚未单独对照 HLSL。exe 需要同目录 `D3D12\` Agility 721 和开发者模式，延用已有隔离 hip-backend 目录。

2026-09-14 COMGR（17,464 字节）、原 HLSL cs6_10 和 MinGW host 均编译通过；未运行 GPU 验证。远端文件：`hip-backend/c32_fast.hsaco`、`c32_fast_ffn_validate.exe`、`c32-fast-oracle/c32_fast_oracle.cso`。

## 最终 half 舍入校准（待复测）

首次 GPU 对照共 11,904 个最终 half 差异，无非有限值。pattern1 的 3,996 处差异全部满足 abs(HLSL)<abs(HIP)，方向无例外，相差相邻 half 一格；指向生产 HLSL `f32tof16` 的 RTZ 与 HIP RNE 不同。新版只将 fast contract 最终转换改为显式整数 RTZ，exact 参考模块保持 RNE。新增诊断 raw_output=2 返回转换前累加器，FFN host 保存为 `*-hip-pre-round.f32`。

源码/可执行名已消除与 attention probe 的冲突：`c32_fast_ffn_validate.cpp` / `c32_fast_ffn_validate.exe`。新版 HIP 模块 21,944 字节，已编译，尚待主进程复测。


## RTZ 复测与 map3 扩展

`release/HIP/c32-fast-ffn-rtz-validation.log`：RTZ 修复后的三个 pattern 全部 bitdiff=0、invalid=0。普通残差路径已在这些输入上与真生产 FAST3 HLSL 逐位一致。

新增 `c32_ffn_contract_fast_map3(input, hidden, fw, output, tokens, raw_output)`，launch 与普通 contract 相同。残差 scale 依次拆成 `s0=R(scale)`、`s1=R(scale-s0)`、`s2=R(scale-s0-s1)`，构成三份对角 FP8 矩阵；从零 seed 做三次 K32 WMMA，再接四次 contract K32 WMMA，末尾 RTZ。没有以普通乘法替代这条路径。

原始 raw tile 与对应 F(main) 都可以作为新导出的输入，前提是量化结果 F(input) 相同、窗口和 shift 已正确映射；expand 与 map3 残差都只消费该 FP8 量化结果。不要把同一层 hidden 当作 input 残差。原 map0 contract 仍要求它自己的原始残差值，不能因为 map3 可量化而一起改线。

构建原 HLSL 的 map3 分支：`build_c32_fast_oracle.ps1 -Map3`，输出独立 `c32_fast_oracle_map3.cso`；MAPPED_INPUT=1、运行常量 map_mode=3，其余 FAST3/precise/sat 宏保持。验证：

```text
c32_fast_ffn_validate.exe ASSETS c32_fast.hsaco c32_fast_oracle_map3.cso PREFIX map3
```

host 按原 NativePreblockRuntime 字节布局打包三份对角矩阵，与 HIP 内部 scale 分解独立；使用同一份 raw tile 输入和三组 pattern。2026-09-14 新模块 37,160 字节、HLSL map3 和 host 均编译通过；map3 GPU 数值尚待主进程验证。

map3 GPU 复测（2026-09-14）：三个 pattern 最终 FFN 全部 bitdiff=0。该三对角 WMMA 残差实现已在这组生产 HLSL map3 对照上通过。

Map3 GPU validation now passed all three patterns bitwise (`release/HIP/c32-fast-map3-validation.log`); no nonfinite values. The ordinary residual and diagonal-matrix residual are separately verified entries.


## map3 scale 打包契约修正（2026-09-15）

R 是 NativePreblockRuntime 的 `e4m3r`，**并非一般 F()**：当绝对值小于1/64时，q=RNE(abs(v)×512)，然后强制q≤7，不允许进位到8。GPU与host现均遵循该规则；正常FP8激活量化F()不改。

真实 block2/3/4/67/68/69 的32个scale中，分别1/1/2/1/1/2个通道的三part分解改变。block4 channel21、block67 channel22、block68 channel30的三part和各增加1/512；其余5个通道的和不变。详细值见 `release/HIP/map3-scale-packing-audit.json`，可用 `audit_map3_scale_parts.py ASSETS --output REPORT` 重算。不能仅凭这些变化就认定整网误差根因。

validator新增可选block：`... PREFIX map3 67`；省略默认block1。之前三pattern通过记录只覆盖block1，不能代表所有生产block。两端修复后模块38,312字节、MinGW host均编译通过，扩大GPU对照待主进程执行。

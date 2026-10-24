# C32 GPU reference ABI

`c32_reference.hip` 是逐阶段 scalar GPU 数值参考，不是 WMMA 性能后端。不包含第 0 块 RGB/noise 前缀。全部 kernel 使用 **block=(256,1,1)**，grid.x=ceil(下表线程工作项/256)，grid.y=z=1；在同一 HIP stream 中按表顺序提交。全部指针是设备指针，全部激活/权重为 f32，尺寸与 raw_output 为 uint32。禁止输入输出或中间缓冲重叠。

令 T=窗口数×64，输入布局 `[window][token64][channel32]`。W/H 是整个工作网格尺寸，必须为 8 的倍数，且 T=W×H。

| kernel | 参数顺序 | 工作项 | 输出容量（float 个数） |
|---|---|---:|---:|
| c32_ffn_expand | input, ffn_weights, hidden, T | T×128 | hidden T×128 |
| c32_ffn_contract | input, hidden, ffn_weights, ffn, T, raw_output | T×32 | ffn T×32 |
| c32_attn_qkv | ffn, attn_weights, qkv, T | T×96 | qkv T×96 |
| c32_attn_normalize | qkv, attn_weights, normalized, T | T | normalized T×64 |
| c32_attn_scores | normalized, attn_weights, ex, windows | windows×4096 | ex windows×4096 |
| c32_attn_probabilities | ex, prob, windows | T | prob windows×4096 |
| c32_attn_av | prob, qkv, av, windows | T×32 | av T×32 |
| c32_attn_project | ffn, av, attn_weights, raw, T, raw_output | T×32 | raw T×32 |
| c32_finish | raw, main, down, W, H | W×H×32 | main W×H×32；down (W/2)×(H/2)×32 |

`raw_output=1` 保留 H() 后、F() 前的原始结果，0 则应用 F()；对应 HLSL RAW_OUTPUT。需要原始输出送 finish 时，两处选 1。qkv 排列 `[part3][T][32]`：Q/K 是 H()，V 是 F(H())；normalized 只有 Q/K，排列 `[part2][T][32]`。ex/prob 排列 `[window][query64][key64]`。finish 将 tile-major raw 转为 raster HWC，同时对未经 F() 的 raw 做原顺序 2×2 池化。

权重偏移（单位 float）：

- FFN 共 8736：RAW_INPUT 不用前 512；expand `[128][32]` 在 512；contract `[32][128]` 在 4608；残差 32 个系数在 8704。
- attention 至少 8225：Q/K/V/projection 的 `[32][32]` 分别在 0/1024/2048/3072；query-key 偏置 `[64][64]` 在 4096；Q 归一化 scale 在 8192；残差 32 个系数在 8193。

数值顺序取自 `preblock_input_mix.hlsl::raw_ffn_shared`、`preblock_attention_core.hlsl` 非 wave 分支及 `preblock_finish.hlsl`。保留 half-square 修复、残差 midpoint 修复、位操作 exp 近似、parity/lane denominator 树、AV 两个 32-key 组的逐组 H()；没有替换为通常的 exp/softmax。源文件禁用 FMA contraction 和重关联。rsqrt 使用 gfx1201 builtin `__builtin_amdgcn_rsqf`，其跨 API 最后几位差异仍需 GPU 对照确认。

H() 用整数实现 IEEE binary16 RNE；F() 为有限饱和 E4M3 RNE。主机直接调用同一份源函数，对 263,488 个有限 f32 样本（包括全部有限 f16）与 numpy half、独立 E4M3 格点比较通过。输入、权重及中间值的数值比对以有限域为前提，不用 NaN 相等掩盖错误。

2026-09-14 COMGR 3.0 编译通过，未运行 GPU kernel：

```text
D:\DLSSNR-Lab\rtc_compile.exe D:\DLSSNR-Lab\hip-c32-reference.hsaco D:\DLSSNR-Lab\c32_reference.hip comgr
```

输出 78,672 字节 ELF gfx1201 code object；同名 `.s` 含汇编。所有 GPU 阶段数值仍待宿主与原 shader 对照，不能以编译成功当作算子验证完成。

## GPU 实测（2026-09-14）

`release/HIP/c32-validation.log`：两组输入的 FFN/raw/main/down 全部 bitdiff=0、numericdiff=0、invalid=0、maxabs=0。每组前三项各 8192 个 f32，down 2048 个；与真实 NativePreblockRuntime cs5_1 标量管线逐位一致。此结果只覆盖这两组 16×16 工作网格输入。

# Production mode5 prefix candidate

独立 `prefix_fast.hip`，不使用旧 noise-table/int27 exact prefix。当前按生产 `native_c32_ffn_fused.hlsli` 的 mode5 路径拆成两个 kernel：

| 导出 | 参数 | grid.x | block.x |
|---|---|---:|---:|
| dlss5_prefix_fast_features | rgbaTiles, historyRaster, features, width, height, seed, temporal | ceil(W×H/256) | 256 |
| dlss5_prefix_fast_project | features, originalFfnWeights8736, prefix, tokens | ceil(tokens/16)×2 | 32 |

width/height 为 8 的倍数，tokens=W×H。rgbaTiles 是 `[tile8x8][64][RGBA]` f32，historyRaster 是 `[H][W][RGBA]` f32；features/prefix 均 `[tokens][32]` f32。features 前16通道按原排列，后16为0。temporal=0 时 history 仍绑定但不消费。

Feature 的 RGB 和最终 Gaussian 按明确整数 RTZ 转 half；Gaussian 候选实现采用 AMDGPU native log2×ln2、sqrt、turns 单位 sin/cos，维持原 PRNG、seed 和坐标。这些 native intrinsic 和 D3D intrinsic 的精度关系尚未验证，不能先承诺逐位一致。

Projection 将 features 和原权重作为精确 F16 操作数，运行原生 gfx1201 F16 WMMA，最终 RTZ；不使用 int27 软件乘法替代。features 已在 half 格点，所以操作数 `_Float16` 类型转换不会吞掉任何有意义的舍入边界；最终转换显式实现。

## 真 production oracle

`prefix_fast_oracle.hlsl` 从原 `ffn_fused` 的 mode5 分支摘录同一段 Gaussian/RGB/features/F16 matrix 计算，原顺序和数学保持；只在后续 FFN 之前停止并转储 in0/in1，加一份 ex 中的投影前 features。输出 raw buffer 前 T×32 floats 是 prefix，后 T×32 是 features。权重加载仍是原偏移27776的两个 F16 B tiles，由验证 host 从真实 block0 权重按原布局打包。

```text
prefix_fast_validate.exe ASSETS_DIR prefix_fast.hsaco prefix_fast_oracle.cso OUTPUT_PREFIX
```

W16×H16，两 seed 0/123 × temporal 0/1。每种场景分三层报告：features、喂相同 HLSL features 的独立 HIP projection、完整 HIP prefix。输出同时保存，因此 Gaussian 差异不会掩盖矩阵舍入差异。沿用现有 Agility 721 隔离目录，需要开发者模式，不改驱动。无 noise.f32 依赖。

2026-09-14 HIP COMGR 模块26,024字节、HLSL cs6_10、MinGW host 均编译通过；远端在 `D:\DLSSNR-Lab\hip-backend\`。尚未运行 GPU 数值验证。

## Gaussian 近似归档（2026-09-14）

原始小测试 seed0 两种 temporal 全部一致；seed123 的 features 各1处差异、最大 6.103515625e-5，完整 prefix 分别3/9处差异，最大1.52587890625e-5 / 0.000244140625。喂同一份 HLSL features 的独立 F16 projection 全部逐位一致。

诊断转储确认原因在 sin/cos：seed123 的256个 token 上，a/b/c/d、lnA/lnB、r0/r1、angleC/angleD 全部逐位相同；cosC/cosD/sinD 分别30/37/35处差异，最大绝对差约3.80e-7；raw Gaussian 最大观察差约9.91e-7。token191（x7,y15）的g0：D3D -0.106445156，HIP -0.10644536，恰跨过 half RTZ 边界 -0.1064453125。HIP radians→turns 的额外 f32 舍入与 native trig 的近似，是明确差异来源。

加诊断存储后 compiler context 使 features 差异从1处变成2处，完整 prefix 差异12/19处；因此不做单点修补或承诺跨编译上下文逐位一致。保留为**近似 Gaussian 候选**，不等同于旧 noise-table/int27 exact prefix。上述数字是这组输入的观察上限，不是所有seed/输入的数学误差界。诊断文件为 prefix_fast_diagnostic.{hip,hlsl,cpp}，并非生产接口。

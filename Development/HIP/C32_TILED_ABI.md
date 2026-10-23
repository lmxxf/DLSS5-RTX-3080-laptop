# C32 LDS tiled candidate

独立的 `c32_tiled.hip` / `c32_tiled.hsaco`，不改已有模块或全网 host。仅优化 FFN expand/contract、QKV、projection 四个矩阵阶段。外部参数顺序和 f32 布局与 scalar reference 相同，导出名后缀为 `_tiled`。

令 B=ceil(tokens/64)，所有 grid.y=z=1：

| kernel | grid.x | block.x | 每 block 输出 |
|---|---:|---:|---|
| c32_ffn_expand_tiled | B×2 | 512 | 64 tokens ×64 channels |
| c32_ffn_contract_tiled | B | 256 | 64 tokens ×32 channels |
| c32_attn_qkv_tiled | B×3 | 256 | 某一 part 的 64 tokens ×32 channels |
| c32_attn_project_tiled | B | 256 | 64 tokens ×32 channels |

QKV 的 block 顺序为 part 优先：part=block/B，token 起点=(block%B)×64；输出仍为 `[3][tokens][32]`。末尾 token 读取补零、输出遮罩，所有线程仍参与 barrier。各 kernel 的参数顺序见 C32_REFERENCE_ABI.md。

每个 K32 分组以连续四个 f32 为一组，两次硬件 packed FP8 转换后存一个 LDS uint。输入 64×32 与权重 N×32 在 block 内只装载/转换一次，多个 wave 复用；WMMA 直接从 LDS 每次取两个 uint 作为八个 K 元素。进入转换前有限饱和到 ±448。真实矩阵权重应已精确处于 FP8 格点。

Contract 仍是每组 K32 从零 seed 做两次 K16 WMMA，再执行独立 H(acc+sum)；projection 保留 half_add_midpoint。H 使用 `HIP_ISA_HALF` 的两条内联 v_cvt asm，保留不能优化消失的舍入边界。无普通 `_Float16` 转换替代。

COMGR 编译通过（2026-09-14）：31,536 字节。expand：LDS 4096B、20 VGPR；contract：3072B、46 VGPR；QKV：3072B、20 VGPR；projection：3072B、22 VGPR。全部 private segment=0。尚未 GPU 验证或测得收益。

独立验证 host：

```text
c32_tiled_validate.exe ASSETS_DIR REFERENCE.hsaco WMMA.hsaco TILED.hsaco OUTPUT_PREFIX [repeats=20]
```

针对 tokens=64/80/256/4096，逐阶段与 scalar reference 比较 hidden、FFN、QKV、projection，保存双方 f32 和 bitdiff/invalid/maxabs。80-token 用例专门测末尾遮罩。4096-token 用例另外以 HIP events 对比旧 wave-per-tile WMMA 和新 tiled kernel 的各阶段 GPU 时间，三次预热后重复指定次数；这是算子微基准，不是整网帧率。host 已编译并放远端 `D:\DLSSNR-Lab\hip-backend\c32_tiled_validate.exe`，GPU 测试由主进程串行执行。

# C32 WMMA ABI

`c32_wmma.hip` 的六个 kernel 使用 gfx1201 原生 FP8 WMMA，不含标量 GEMM 回退。输入、权重、输出仍为 f32，与 scalar reference 模块互通；矩阵元素在装载时转换为 FP8，尚未预打包或跨输出块缓存权重。性能未测，不能把它当作已经加速的完整 C32 后端。

权重必须是现有 8736 个 f32 布局，其中 expand/contract 矩阵必须能精确表示为有限 E4M3；验证 host 检查这一条件，不能把额外权重量化误差藏起来。残差系数保留 f32。tokens 是 uint32。

统一 launch：`grid=(ceil(work_items/256),1,1)`、`block=(32,1,1)`，每个 wave 输出 16×16 tile。tokens 必须是完整窗口数×64。

| kernel | 参数（顺序同 scalar） | work_items |
|---|---|---:|
| c32_ffn_expand_wmma | input, weights, hidden, tokens | tokens×128 |
| c32_ffn_contract_wmma | input, hidden, weights, output, tokens, raw_output | tokens×32 |
| c32_attn_qkv_wmma | input, weights, qkv, tokens | tokens×96 |
| c32_attn_scores_wmma | normalized, weights, ex, windows | windows×4096 |
| c32_attn_av_wmma | prob, qkv, av, windows | tokens×32 |
| c32_attn_project_wmma | input, av, weights, output, tokens, raw_output | tokens×32 |

attention 布局与 C32_REFERENCE_ABI.md 一致。QKV 分 part；score 每窗口 4×4 个 tile；AV 每窗口 4×2 个 tile。QKV normalize、probabilities 和 finish 仍调用 scalar reference 模块。加载时硬件 FP8 转换前夹到 ±448；attention 的前 4096 权重也必须已在 FP8 格点，host 会检查。

输入 `[tokens][32]`；hidden `[tokens][128]`；output `[tokens][32]`。输入中 token 顺序仍沿用 tile-major 外层布局。当前窗口 ABI 要求 tokens 为 64 的倍数；当前验证用 tokens=256。

每个 wave 算 16 token × 16 output。lane%16 是 A 的行及 B 的列，lane/16 选择 K 的八元素半块；输出每 lane 八个元素，对应行 `lane/16*8+element`。

Expand 的 K32 从零种子依次跑两个 K16 WMMA，然后 H、原 polynomial、F。Contract 的每个 K32 分组也从零种子开始两次 WMMA；分组结束后才执行 `acc=H(acc+sum)`。残差先单独 H，不能塞进首次 WMMA 的 C 参数。保留 FMA contraction 禁用；矩阵内部累加顺序与标量 GEMM 的差异必须实测。

验证命令：

```text
c32_validate.exe ASSETS_DIR c32_reference.hsaco OUTPUT_PREFIX c32_wmma.hsaco
```

前三参数的原 D3D12-vs-HIP reference 验证保留；第四个可选 module 新增 hidden、完整 FFN、以及输入 scalar hidden 的独立 contract 比较。每项记录 bitdiff/numericdiff/invalid/maxabs，并保存 `-wmma-*`、`-reference-*` f32，避免 expand 差异掩盖 contract 本身的问题。

2026-09-14 已通过本机 COMGR 编译，产物 `D:\DLSSNR-Lab\hip-backend\c32_wmma.hsaco` 79,032 字节；汇编确认 FP8 WMMA 指令，expand 33 VGPR、contract 51 VGPR，两者 private segment=0。尚未执行 GPU 验证，不声明逐位相同或速度收益。

## GPU 实测（2026-09-14）

两组 16×16 输入均通过：WMMA hidden（每组 32768 个 f32）、完整 FFN（8192）、独立 contract（8192）全部 bitdiff=0；原 D3D12-vs-HIP FFN/raw/main/down 也继续全 0。这里只证明这些输入下数值一致，尚未测吞吐收益。

## attention 扩展（待 GPU 验证）

新增 QKV、score+位映射 exp、AV、projection 的原生 FP8 WMMA。AV 每 K32 从零累积两次 K16 后做 `H(acc+sum)`；projection 继续用原 `half_add_midpoint` 加残差，未把残差种入 WMMA。COMGR 编译通过，模块 146,504 字节。

验证 host 已同步 flat launch，并新增 QKV、normalized、ex、prob、AV、raw 的中间输出比较；新增阶段尚未 GPU 执行。早先“两组全 bitexact”记录只证明上一版 FFN，不能代替本扩展的验收。

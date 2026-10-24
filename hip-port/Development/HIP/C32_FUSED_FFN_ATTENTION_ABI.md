# Production C32 FFN + attention fused candidate

独立 `c32_fused_ffn_attention.hip`；不改 graph、prefix、finish。输入已完成窗口/shift映射的 f32 tile-major `[windows][64][32]`；真实权重 fw8736、aw8225。

```text
c32_fast_ffn_attention_fused(input, fw, aw, raw_output_buffer, windows, residual_mode, raw_output)
```

所有尺寸/模式为uint32。residual_mode只能0或3，含义与已校准fast FFN模块相同；raw_output=1输出attention最终RTZ，0再F。launch `grid=(windows,1,1), block=(128,1,1)`。

LDS复用：

- packed输入64×36byte与expand权重128×36byte，合用原norm区6912B。
- hidden64×132byte，临时用原raw/ex区8448B。
- expand结束后，contract权重32×132byte复用norm后4608B，输入区仍保留。
- map3残差严格使用真实e4m3r（subnormal q≤7），三份对角FP8矩阵WMMA；普通mode0使用SAT后的原input×scale。
- contract四K32持续累加，最终RTZ后FFN保存在额外64×34half（4352B）。它在后续QKV及attention projection残差中使用；存half没有额外损失。
- FFN完成后，6912B和8448B归还已验证packed attention算法。总LDS19712B。

所有阶段及不同stride复用前有显式WG barrier。不写global hidden或FFN，最终只写attention output。

COMGR编译（2026-09-15）：55,512B，LDS19,712B、165 VGPR、private segment0。寄存器用量上升，性能待测。

验证器：

```text
c32_fused_ffn_attention_validate.exe ASSETS FAST_FFN_MODULE SIX_STAGE_ATTENTION_MODULE FUSED_MODULE PREFIX [repeats20]
```

以已经分别对真生产HLSL验证的fast FFN二阶段 + attention六阶段组合为裁判，本probe不重写或重跑HLSL。block1/block4、tokens256/4096、两pattern、残差mode0/3共16组，保存chain/fused最终raw及参考FFN。block4大T的两mode另外用HIP events比较八次kernel launch与一次融合launch；无阶段间CPU同步，预热3次。

必须传入修正subnormal q≤7的最新版fast FFN模块，避免把旧打包误差当作融合差异。编译和上传完成，GPU正确性/计时待主进程串行执行。

2026-09-15: all16 chain comparisons passed. LargeT isolated timings varied; choose based on whole-frame measurements, not compilation metadata.

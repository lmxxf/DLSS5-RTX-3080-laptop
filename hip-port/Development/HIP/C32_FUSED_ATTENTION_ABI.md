# Single-window production C32 attention candidate

独立 `c32_fused_attention.hip`，保留六阶段 `c32_fast_attention.hip` 作为裁判，不改 graph。当前只融合 attention，FFN、prefix、finish 不包含在内。

```text
c32_fast_attention_fused(raw_ffn_input, aw8225, output, windows, raw_output)
```

所有指针为 f32 GPU buffer；输入和输出 `[windows][64][32]` tile-major；aw 是原8225个 f32 权重，矩阵权重已在有限 FP8 格点。windows/raw_output 为uint32；raw_output=1输出最终RTZ，0额外量化F。

Launch：`grid=(windows,1,1)`，`block=(128,1,1)`。每个 window 一个 workgroup，四个 wave 各处理16个query。

QKV raw、norm、exp、prob、AV 全留 LDS；QKV使用三平面共24KB，ex/prob复用16KB，Q平面在scores之后复用为AV。最终只写output。所有阶段之间有workgroup release/barrier/acquire；没有跨workgroup共享数据。

计算保持已验证六阶段的日程：QKV为FP8 WMMA rawf32，norm平方Cast F16再两次K16 WMMA求和，rsqrt不插额外H；score为FP8 WMMA、偏置、原位exp，affine显式RTZ；概率分母为4次F16 K16、F(ex/inv)；AV是4次FP8 K16连续累加后F；projection再两次FP8 K16，最后RTZ(sum+raw*scale)。没有替换为通常softmax或旧exact日程。

COMGR编译通过：69,424字节，LDS40,960字节、83 VGPR、private segment0。LDS占用较高，速度必须实测，不能由融合本身推断。

独立验证：

```text
c32_fused_attention_validate.exe ASSETS SIX_STAGE_MODULE HLSL_ORACLE_CSO OUTPUT_PREFIX FUSED_MODULE
```

保留原两pattern的真HLSL六阶段比较，新增最终fused对HLSL/六阶段双对照。另tokens4096对比六阶段最终输出，保存raw f32；三次预热后用HIP events测20次完整attention，不在六阶段之间加CPU同步。命令所需exe/hsaco已在远端hip-backend，尚未GPU运行。

## 首轮实测与 padding 候选

首版两pattern对真HLSL及六阶段全部bitdiff0，tokens4096也全0。该微基准六阶段0.0205ms、融合0.04761ms，融合暂时更慢。

当前源码仅增加LDS行padding：QKV/raw/norm/AV仍为f32，stride32→33；ex/prob仍为f32，stride64→65。尚未变成FP8/half packed存储，避免把bank冲突与数据重排混在同一轮。有效元素对应的索引全部同步；全体LDS地址与16行同列bank唯一性通过CPU检查。

新候选 `c32_fused_attention_padded.hsaco`（69,808B），LDS41,984B、83VGPR、private0。原 `c32_fused_attention.hsaco` 二进制保留用于对比。外部ABI及validator不变，替换最后模块参数即可；padding版本尚待GPU复测。

## Packed LDS 候选（2026-09-15）

padding版全正确，但同轮微基准六阶段0.02104ms、padding融合0.046595ms，纯行padding没有明显收益。

新增独立 `c32_fused_attention_packed.hip`，导出和外部ABI保持：

- raw只保留一个64×33 float平面，每个part完成norm后转到独立packed平面。
- raw平面随后复用为64×66 half的ex，共8448B。
- normalized Q/K/V共3×64×36 bytes，6912B。
- scores完成后，Q/K的前4608B复用为64×68byte概率（4352B），V平面保留。
- AV两个column fragment都先存在寄存器；所有wave完成概率读取后执行WG barrier，再将AV写回Q平面，避免新旧row stride交叉覆盖。

所有有效地址及live V不重叠已CPU检查。COMGR产物 `c32_fused_attention_packed.hsaco` 39,472B；LDS由41,984降至15,360B，VGPR由83升至122，private segment0。原始和padding二进制保留。编译通过，尚待原validator的两pattern/large-T正确性与GPU计时，不因LDS降低先断言加速。

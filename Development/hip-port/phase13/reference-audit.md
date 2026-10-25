# Phase13：720p 参考链首次异常定位

唯一默认基线：Phase12 selected，起点41220e0。初始工作树干净。默认图不改；本报告中的 attention400 是隔离诊断开关，不能当成0bit优化部署。

## 结果

异常不是仅存在于旧F32参考：**Phase12自身720p也走同一条异常256 attention路径**。首个异常放大位于block31内的 `vit_attention_fused_256_bytein_bout`，实际token数240。之前head数值范围正常（两链均[-12,12]，RMS约1.67），block31后RMS约22；900p/1080p同位置约1.7。此前把720p的11.6075dB笼统归为“F32坏参考”不够准确，应纠正为**两链共同的720p attention正确性问题，随后精度差被放大**。

不将正常的FP16/F32差异或不同边界表示误读成错误：FP8/half/float均按实际Host分配合同解码。900p C512有padding、用float；720/1080 C512走byte。head/ViT在COMPACT_ALL=0旧F32链中720/900为float，在selected中为byte；比较前分别解码到数值域。原始字节大小、哈希及逐层指标见 `layer-comparison.json/md`。没有安装observer，也没有打开dump_dir，避免它们关闭raw-chain/inter-byte图门控；Stage诊断tap只读取，六次trace最终输出均与各自未插桩输出0bit相同。

## 控制与独立核验

1. 同一720 F32链切C256 split/fused，输出 **0bit相同**。不是C256门控导致本次异常。
2. 从首个ViT调用抓取真实Q/K/V及AV。只在隔离Host把<=256选择改成已有400路径，其它权重、QKV生产者、token数均不变；256/400两次的QKV SHA相同。
3. 独立CPU实现源算法：FP8 QK矩阵乘、源代码clamp/half位映射近似exp、FP8概率×V、half概率分母、E4M3输出。没有拿GPU400当CPU答案。

| 链 | CPU预期AV RMS | 256 AV对CPU RMSE / maxabs | 400 AV对CPU RMSE / maxabs | 400字节一致率 |
|---|---:|---:|---:|---:|
| Phase12 FP16 | 2.683435 | 33.287352 / 446.75 | 0.027869 / 1.0 | 98.8261% |
| Phase1 F32 | 2.643835 | 33.331681 / 446.75 | **0 / 0** | **100%** |

CPU参考用double累加后舍入到F32；FP16 Tensor Core/RCP近量化边界差异允许存在，所以不要求FP16对CPU逐位相同。F32400的全部245760个AV字节对CPU逐位一致，足以排除“只是合理精度差”的解释。原始输入/AV哈希在 `reference-provenance.json`，脚本 `attention_cpu.py`，结果 `attention-cpu-results.json`。

均匀Q=K=0,V=1的额外GPU探针在n=16/240/256、两条链、256/400全部通过，见 `attention-uniform-results.json`。所以**不声称已经证明n%64尾块错误**。当前定位粒度为旧256 LDS转置attention路径；400使用transposed-score路径。具体哪条地址/分母/布局指令错，尚待更细的单点探针，不把推测写成真凶。

4. 改走400后的两条720p诊断整网差异恢复到可见43.577948dB、maxabs0.0509355。这是**修正图之间的诊断差异，不是当前默认720p的绝对PSNR**。
5. 同一诊断Host/F32链复跑900p/1080p，对归档F32 gold均 **0bit**（`f32-calibration.json`）；修正开关只在<=256选择上作用，不改变这两档路径。

## 默认与下一步

本轮要求默认三档相对Phase12严格0bit，故不把400路由修正混入性能优化。720p当前默认仍无可信绝对F32 PSNR；不能用11.6075dB坏比较淘汰0bit候选，也不能把修正图参考冒充默认图gold。状态 `f32-reference-status.json`。

Phase14建议优先把该问题作为**允许输出变化的独立正确性修复**：用坐标可识别的Q/K/V单点矩阵进一步定位256路径转置/归约，验证修复对CPU与400的关系，再重新建立720金标准。届时需要单列新输出基线，不覆盖Phase12/13旧样本。

## 复现

```bash
python3 Development/hip-port/phase13/build_diagnostic_host.py
python3 Development/hip-port/phase13/trace_layers.py
python3 Development/hip-port/phase13/analyze_trace.py
python3 Development/hip-port/phase13/reference_calibrate.py
python3 Development/hip-port/phase13/attention_probe.py
python3 Development/hip-port/phase13/attention_cpu.py
```

实际attention抓取及legacy256/forced400四次运行参数见根README的命令入口（`run_attention.py`）。所有诊断输出在被忽略的artifacts，源码/模块/数据哈希在JSON。约1.24GB原始层dump已在统计及完整SHA归档后删除，只保留head/block31及实际QKV/AV小样本；重做逐层分析需先重跑trace_layers。未改共享资产、旧模块或Windows部署。

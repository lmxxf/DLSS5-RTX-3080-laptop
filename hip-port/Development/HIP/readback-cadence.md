# 读回节奏与GPU频率诊断

benchmark_live_capture.cpp增加末尾参数edges_only（默认0）。值1仍逐帧还原同一输入并执行完整推理/历史更新，只跳过中间帧的读回及CPU统计，首尾照常保存。CSV新增checked字段；未检查帧统计留空，checked=0。计时每帧都保留。默认0仍全帧检查；首尾模式不是完整正确性验收，invalid_total仅累计实际检查的帧。

validate-hdr.ps1以-EdgesOnly 1传入新参数，输出sampled_finite=1 checked_frames=2，不能误读为全部40帧有限。默认拒绝缺失检查，兼容老程序无checked字段的全帧CSV。最终hash必须仍匹配该后端参考。

新程序分别以DLSS5_COMPARE_HLSL或DLSS5_USE_HIP编译，未启用LIST_TIMING宏；保存为benchmark_hlsl_edges.exe和benchmark_hip_edges.exe。compare-readback-cadence.ps1执行0/1/1/0、40帧、排除前5帧，读取相同rebind-async-flags，配套mh-input-mapped-release-modules。并行ADL只读250个样本，采样按adapter0和gfx activity>50%筛选；每轮只有4–9个活跃样本，范围包含启动和收尾，不是逐帧精确频率。

| 后端/模式 | 两轮热中位ms | 核心频率中位MHz | GPU负载中位% |
| --- | --- | --- | --- |
| HLSL全帧读回 | 26.577 / 26.588 | 1794 / 1786 | 65 / 65 |
| HLSL首尾读回 | 16.736 / 16.686 | 2799 / 2990 | 93.5 / 95 |
| HIP全帧读回 | 28.454 / 27.166 | 2735 / 2813.5 | 77.5 / 83.5 |
| HIP首尾读回 | 26.290 / 26.365 | 2998 / 2997 | 99 / 99 |

最终图像在各后端内部四轮保持原hash（HLSL C7C2F49D…、HIP FEEA9EF3…）。所有全读回帧有限；首尾模式仅检查两帧。读回本来在计时区间外，但改变整体负载间隔，明显影响频率和后续帧的计时，不能当成计时器直接少算了读回。

当前同样较连续模式下仍有约9.6ms后端差距，不能用旧的26ms/26ms认定追平。历史18.8ms没有同期遥测，不能重建当时精确频率；本实验只确定当前可复现的因果因素。后续性能对照应采用一致读回节奏，并保留独立全帧正确性验证。所有变化仅实验室程序，游戏和驱动设置未变。

日志release/HIP/hlsl-cadence-summary.log、hip-cadence-summary.log、相应-adl.log及readback-cadence-summary.json。

# HLSL命令列表计时诊断

仅编译诊断程序时定义`DLSS5_BENCH_LIST_TIMING=1`，不启用游戏配置：

```sh
x86_64-w64-mingw32-g++ -w -DDLSS5_COMPARE_HLSL=1 -DDLSS5_BENCH_LIST_TIMING=1 -std=c++17 -O2 -static -municode -Isrc Development/HIP/benchmark_live_capture.cpp -o /tmp/benchmark_hlsl_lists.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

将程序放在实验室目录（需已有D3D12 Agility运行时），用validate-hdr.ps1指定Runner，使用rebind-async-flags.txt。游戏须退出。默认batch_submits=2时网络6个列表，每列表开头/结尾插时间戳，末尾额外resolve及Flush；不超过64个列表。该Flush可能改变后处理提交重叠，故仅用于定位，不当性能优化。

LIST_TIMING字段：in_list_ms为列表内区间之和（含GPU内存等待、可能的抢占等，非纯ALU忙时）；gaps_ms为列表之间区间之和；record_submit_ms为CPU记录/提交循环时间，可与GPU执行重叠，不能相加；wall_ms还包含resolve与完成等待。计时只覆盖神经网络，不含前后codec等。

2026-09-15，40帧、去前5，35样本中位：列表6，in_list25.83108ms，gaps0.06636ms，record_submit0.543ms，wall26.373ms。完整帧热中位27.001ms，输出C7C2F49D…与既有HLSL一致。当前慢值发生于列表执行区间，不能仅归于CPU记录或列表间空档；尚不能区分频率、驱动、抢占、shader实际路径等。历史18.8ms未重现，不据此判HIP达到目标。

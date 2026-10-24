# 只读AMD遥测

read-adl-telemetry.cpp使用驱动提供的atiadlxx.dll，动态调用ADL2查询接口，不调用时钟/功耗/电压设置API。编译依赖AMD display-library的include/adl_structures.h和adl_defines.h（不随本工具复制）。

来源：[AMD结构定义](https://github.com/GPUOpen-LibrariesAndSDKs/display-library/blob/master/include/adl_structures.h)、[传感器编号和单位](https://github.com/GPUOpen-LibrariesAndSDKs/display-library/blob/master/include/adl_defines.h)、[API文档](https://gpuopen-librariesandsdks.github.io/adl/overdrive8_8h_source.html)。ADL2_New_QueryPMLogData_Get已被AMD标记deprecated，当前测试驱动仍返回受支持数据；其他驱动可能需要更新API。

```sh
x86_64-w64-mingw32-g++ -w -std=c++17 -O2 -static -I/tmp/dlss5-adl Development/HIP/read-adl-telemetry.cpp -o /tmp/read-adl-telemetry.exe
```

参数为样本数，默认1，上限600，每200ms采样。必须检查status及每项supported，unsupported不是测得0。当前RX9070XT出现多个逻辑adapter，不能当成多张卡或合并为独立样本；本轮只统计adapter0。iPresent在SSH环境为0但查询仍成功，工具不据此过滤。

measure-hlsl-telemetry.ps1在实验室同步运行150次采样和HLSL40帧校验，用GetTickCount时间轴标记整个测试起止。负载窗口还包括初始化和收尾，不能把全部样本当热帧。它不修改游戏；游戏运行时拒绝。

本轮完整帧26.872ms、输出C7C2F49D…一致。测试起止tick284568312–284575609，adapter0且gfx activity>50%的8个样本：gfx clock1511–1849MHz、中位1807；edge43–44°C、hotspot47–52°C。ASIC power未支持，不报0W。没有历史18.8ms对应的频率，不能作降频因果结论。

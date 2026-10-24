# 同输入桥接隔离

仅诊断程序定义DLSS5_BENCH_BRIDGE_ISOLATE；生产DLL不定义，不开放诊断接口。构建：

```sh
x86_64-w64-mingw32-g++ -w -DDLSS5_USE_HIP=1 -DDLSS5_BENCH_BRIDGE_ISOLATE=1 -std=c++17 -O2 -static -municode -Isrc Development/HIP/benchmark_live_capture.cpp -o /tmp/benchmark_bridge_isolate.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

measure-bridge-isolation.ps1要求游戏退出，40帧、temporal=0、edges_only=1。先执行完整Frame，再在GPU完成后捕获PostBase真实输入和未平滑的原始网络RGB输出。使用同一Network实例，输入上传一次到HIP私有缓冲，预热10次，再40次Enqueue+stream completion计时，最后读回并与原始RGB逐float位比较。随后释放私有输入/输出，再跑完整Frame40次（去前5），再次比较原始网络输出。无需重新创建模型/权重。

此次完成的三段：full-before24.401ms、pure-HIP24.269ms、full-after24.548ms，原始输出bitdiff0、无非有限值。此前首轮也是full24.480/pure24.2575ms。证明本次no-history输入上，完整前后处理/共享资源/桥接合计没有产生8ms差距。

限制：纯HIP时间含CPU Enqueue和等待，不是仅GPU指令忙时；全流水线与纯HIP使用的缓冲类型不同，不能把差值当单独copy或context-switch成本。未覆盖有history路径，也不是新实机FPS。捕获/上传/最终读回都在pure计时区间外。诊断返回借用资源，只能在单线程持有、已完成GPU工作的Frame上使用。


Graph补充对照：脚本新增-Graph 0/1及-Tag，隔离实验使用独立flags文件，不改全局/游戏配置。Graph1结果full-before24.324ms、pure24.205ms、full-after24.524ms，原始输出bitdiff0、无非有限，graph_stats builds=3/replays=127（完整→私有缓冲→完整的指针变化分别重建）。相对Graph0的pure24.269ms只有小差距，不足解释主要缺口；不是声称CPU提交零成本，而是本测例中它没有构成主要可消除延迟。

# 2026-10-24 mapped 量化与 O4 性能回收实验

> 最新：已剔除跨块/多定义mapped，15/15 O4，天空红绿变号0次，已部署；速度尚未恢复。见[最终回执](安全mapped最终回执.md)。


实现位于 build_quantmapped.py：保持原 mapped 查找、原位置 cvt/pack 的死代码删除、MMA fragment 映射和 bulk 转换；每个连续 MMA run 只对实际使用的 unique low/high 源寄存器量化一次，在 shuffle 前存入临时 qm_qN，而不是覆写原源。其余非mapped操作数仍走原来的解包。

量化先以 FP16x2 max/min 限制到 ±448，再对普通数做低7位 RNE 舍入。对 abs(x)<2^-6 的通道，另用 FP16 add.rn(abs(x),2) 再减2，得到间隔2^-9的E4M3次正规网格，随后恢复符号，并以每通道独立选择及prmt合并。普通数的7指令版本不能单独当作完整E4M3量化。

精度验证：check_quantmapped.py 的独立有限E4M3查表最近偶数参考，对63,488个有限FP16编码穷举零差异；缺少次正规处理的普通数版本有16,368个不匹配。check_quantmapped_gpu.py 从实际生成器抽取同一PTX片段，在RTX3080Laptop实跑打包双通道，各通道63,488个有限编码均零差异，包含负零。未宣称NaN payload及无穷输入语义与原cvt完全相同；本次网络输入输出均须检查nonfinite。

编译脚本对15个Fatbin全部从原版PTX重编；输出独立 nvngx_dlssnr_sm86_quantmapped.dll，不覆盖fast或游戏DLL。O4容量不够时保留原构建器O1回落并在日志中明确记录。

运行脚本 run_quantmapped.py 对 fast 和 quantmapped 依次跑720p平滑天空、900p/1080p原bench场景，各warmup5、测量20。后两档用于与原先相同场景对比性能，不能与天空输入的耗时直接混成分辨率缩放定律。GPU timestamp与wall都保留在日志；两版本依次运行，有温度/频率顺序影响。

## 实测结果：本方案未通过

全量编译只有12/15 O4；0、1、4仍回落O1，2恢复O4。见quantmapped-build.log。

| 分辨率/场景 | 同轮fast GPU median | quantmapped GPU median |
|---|---:|---:|
|1280×720 sky|16.454ms|22.114ms|
|1600×900原bench场景|24.720ms|34.133ms|
|1920×1080原bench场景|32.854ms|47.160ms|

两版本各5帧warmup、20帧测量；全部nonfinite=0。完整回执见quantmapped-results.txt及分辨率日志。

天空仍有104次红绿变号，高频RMS=.02613936；同轮fast为106次、.02763075，只改善约5.4%，没有达到nomapped的0次与约.000104。quantmapped-output.png目视仍有横带。与早先nomapped输出最大差=.17626953，RMSE=.047193073。

这一反证推翻了前一轮“绕过量化就足以解释条纹”的断言。关闭mapped消除色带仍成立，但正确量化后重新走mapped仍出问题，故只能锁定mapped整条取数替换路径有问题，不能把它等同为单纯少做一次量化。需要检查更完整的寄存器/控制流依赖，而不是继续只压量化指令。

补充核验：check_existing_roundtrip_gpu.py 对既有fast FP16->FP8->FP16两个转换助手的组合也做了GPU混合打包穷举，两个通道各63,488个有限输入同样零误差。因此新量化助手与既有助手都通过局部转换检验，差异仍在它们接入网络的位置/取数路径，而非局部有限数转换本身。

expanded寄存器源写入扫描及转换在pack之后的顺序扫描目前未给出实际覆写实例；这些扫描不是CFG证明。不宣称已确定更细的缺陷。

诊断DLL SHA256:1979fc2a162ea4c574cc1e1eb3f75f4780d601265ad49aac5ca830737a36c26f。仅在C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_quantmapped.dll保留，不安装进游戏。当前可消除合成横带的诊断控制仍是nomapped。

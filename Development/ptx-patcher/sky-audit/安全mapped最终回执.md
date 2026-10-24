# 2026-10-24 安全 mapped 修复与部署回执

> 后续控制实验已恢复原槽位15/15 O4及15.83/24.47/32.04ms，并替换部署。本文件保留上一轮记录，最新见[去量化回执](去量化控制变量回执.md)。


正确性修复已完成并部署，15/15 Fatbin 全 O4；原速度尚未恢复。未启动游戏，真实游戏天空的观感仍待实际游玩确认。

## 根因与源码

旧 `fp8_pack_sources` 只统计特定 cvt/pack 匹配次数，未统计寄存器所有定义；FB5 `cc_vit_attention_fp8` 的 `%r1352` 实际有 `ld.weak.global.ca.v4.u32` 和 fallback `mov.b32` 两种定义，错误 mapped 在有效数据路径上把显存值替成了 fallback 来源。精确量化不能修复这种取错值。

`ptx_mapped.py` 解析标量、花括号向量目的操作数及内联分号指令，保留定义位置/谓词；以标签和控制转移建立基本块。仅保留 pack目标、FP8两路中间值、FP16来源均单定义，且源定义、转换、pack、MMA均位于同一基本块的映射。无法证明就走原FP8寄存器解包路径，跨基本块使用也拒绝。

按旧mapped的实际MMA操作数使用统计：

|Fatbin|保留合法使用|剔除使用|主要原因|
|---|---:|---:|---|
|0|16960|2944|跨块转换1216、跨块使用1216、pack多定义512|
|1|5120|4096|源非本块2560、跨块转换768、跨块使用768|
|2|3840|1536|跨块转换768、跨块使用768|
|3|5376|0|该子集满足局部检查|
|4|1152|640|源非本块512、跨块使用128|
|5|768|192|pack目标多定义；含%r1352反例|
|6|0|0|原本无mapped实际使用|

合法mapped仍保留量化：每run每unique源一次，普通数RNE和E4M3次正规网格均正确；使用双通道比较及lop3选择，实际GPU两通道各63,488个有限FP16编码零误差。未宣称任意NaN payload语义完全等价。

`dlssnr_patcher.py` 与 `build_sm86_dlls.py` 都接入同一资格检查。构建入口不再依赖/tmp源文件，原版DLL SHA256固定为 `2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f`。

## 15/15 O4 与 PE 容量

FB0/1/2/4 的O4仍超过原槽位；实际构建中全部保持O4，通过新增 `.dlssptx` PE节存放这些Fatbin，修改每个唯一、已核验的宿主RIP相对LEA引用。其余Fatbin原位写入。DLL从7节变8节，全部15个blob位置、Fatbin魔数及4个引用目标均核验；NGX Init/Create/Evaluate实测成功。这里没有声称代码已缩回原槽位。

构建回执：safe-build.log；布局清单：safe-pe-manifest.json；生产可复现命令见 ../README.md。

## 天空与速度

同机、preset2、style1；warmup5，测量20；天空输入1280×720 RGBA16F，零运动、恒定远深度。两版依次跑，有温度/频率顺序影响。

- 旧fast：每行R-G变号106次，高频RMS=0.027630752。
- safe：变号0次，高频RMS=0.00010052723，降低约275倍。
- safe相对早先nomapped输出maxabs=.009277344、RMSE=.0011511096；不宣称与nomapped逐位一致。O4/O1与浮点运算优化会影响数值。
- safe-output.png 已目视检查，无原先的密集红绿横带。

|分辨率/场景|旧fast GPU median|safe GPU median|
|---|---:|---:|
|1280×720天空|15.972ms|23.751ms|
|1600×900原bench场景|24.563ms|33.034ms|
|1920×1080原bench场景|31.957ms|43.418ms|

全部nonfinite=0。900p/1080p不是天空场景，不与720p混算分辨率缩放比。性能目标16/24/31ms尚未达到；15/15 O4不等于原来错误mapped路径的执行成本。见safe-results.txt及各safe分辨率日志。

## 已部署与恢复

已更新源码与Development/DevHistory.md；未提交git。已替换：

- C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_fast.dll
- C:\XboxGames\Onimusha- Way of the Sword\Content\nvngx_dlssnr.dll

两处安装后重新读取SHA256均为 `7c8631871811c8bb3d98f87778917e9fc92f010d3db304f8f9bef0f822f16bf7`。

旧fast与旧游戏DLL相同，SHA256均为 `f94656391b63dc744c0275b8f2cc5c1254ac104d11dbc44222981fa31e64237d`，已保留一份核验备份及哈希门控的双目标恢复脚本。恢复命令（先关闭游戏，在WSL运行）：

```bash
python3 /mnt/c/DLSS5-5090-dll/backups/20261024-safe-mapped/restore.py
```

恢复说明同目录 `恢复说明.md`。未改OptiScaler.ini。

6项资格检查回归测试通过，涵盖多行向量加载、内联向量写入、跨基本块转换/使用、谓词控制与合法局部映射；py_compile和git diff --check通过。

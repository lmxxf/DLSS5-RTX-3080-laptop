# 异步描述符重绑回归（2026-09-15）

`queued_frame_probe.cpp`在完整NativeGameFrame链上排队12帧，对每帧保存独立快照，最后统一等待读回；前2帧后排空一次排除冷启动计时。输入为1296×720 RGBA16F真实菜单捕获，内部900P，配套vit-layout-modules。源资源始终存活，测试重点是SRV原位改写与GPU读取之间的竞态。

编译当前版本：

```sh
x86_64-w64-mingw32-g++ -w -DDLSS5_USE_HIP=1 -std=c++17 -O2 -static -municode -Isrc Development/HIP/queued_frame_probe.cpp -o /tmp/queued_frame_fixed.exe -ld3d12 -ldxgi -ld3dcompiler -ldxguid
```

旧版对照使用c5558fe的src/native_game_frame.h和src/native_temporal_feed.h，其余源码及本探针保持相同。将旧头文件放入独立include目录，其余头文件链接到当前src，以上命令改-I目录并输出queued_frame_old.exe。不要在生产代码增加不安全开关。

两exe及run-queued-frame.ps1、test-rebind-lifetime.ps1放入远端D:\DLSSNR-Lab\hip-backend。需要已有live-menu-before.f16、compare-hip-sync-flags.txt、vit-layout-modules及network-720p资产。关闭游戏后在PowerShell运行：

```powershell
& D:\DLSSNR-Lab\hip-backend\test-rebind-lifetime.ps1
```

脚本执行11组进程、7项比较。颜色轮换、运动纹理轮换的旧异步输出应与同步不同；新版分别恢复一致；两者同时轮换也应一致。固定纹理只交替内容时旧同步、旧异步和新异步均应一致。比较的是全部12帧拼接数据，不只是最后一帧。旧错误hash受调度影响，不应写死；若旧错误未复现，脚本会报错，需要检查排队条件，不能自动视为通过。

本轮7项均通过。正确SHA256：

| 条件 | 全帧hash |
| --- | --- |
| 颜色轮换／内容交替 | 411DF44CD72093504699AD1B19D1109988C25976F859F17B7181DB1DE90B7CD1 |
| 运动纹理轮换 | F687BC966FA137044A057A55E6AAB6DD8C0FF87A315BBF0F290FEBFCE11D6435 |
| 颜色及运动轮换 | 43712DDEE8EA04AD645BB2A1AEC55F60839F27C0C3E293A94DC2A5EC35399DFF |

独立HDR40帧验证同步／异步热中位39.375／38.833ms，最终hash均FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58且全有限。短轮离线数据不代表稳定速度收益；实机异步和overlap性能另行验证。游戏avg_ms_per_frame是处理帧间隔，不能和上述推理计时直接相减。


## 颜色绑定快取回归

当前头文件编译探针时输出`queued_frame_cache.exe`，与上一修复版（005bced／e78edb1头文件）构建的`queued_frame_fixed.exe`对照。将`test-binding-cache.ps1`放入相同远端目录运行。探针rotate=2新增12张不同纹理，超出8组绑定快取，逐帧内容仍与两张交替相同，因此可沿用原同步hash检查淘汰正确性。五项正确性测试通过后执行8轮ABBA，比较每次后10帧平均耗时；本轮37.52715→37.16005ms为各方案4次读数的中位数。运动SRV轮换仍采用完成等待，未在本次优化。


## 运动绑定快取回归

当前探针输出queued_frame_motion_cache.exe，上一颜色快取版fec7383构建queued_frame_cache.exe。运行test-motion-cache.ps1，沿用同一实验室资产。temporal=3新增12张不同motion纹理，内容与temporal=2相同，结合rotate=2测试两套快取淘汰；8轮ABBA使用颜色+motion轮换，比对颜色快取与双快取。五项正确性及全部ABBA输出hash通过，耗时37.87255→37.60930ms（各方案4次热帧均值的中位）。

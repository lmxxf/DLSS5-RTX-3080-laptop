DLSS5 RTX30 0.1.0 - Magpie 原生 PTX 正式包

直接运行本目录Magpie.exe，默认预设DLSS5-RTX30-PTX：
原生DLSSNR（Preset2、Style1、31块Small）-> NVIDIA原生DLSS_SR。
720p窗口捕获后由NR同尺寸重打光，再由DLSS_SR放大到屏幕。
无ReShade dxgi.dll、无dlss5-amd.addon64、无DLSS5-AMD外置权重目录。
不要把旧包的ReShade/add-on/权重目录混拷回来。

Magpie.exe已做最小Preset2补丁：原后端写死Preset0，JSON不能改变。补丁只改Preset Set调用及对应日志，前后SHA/地址见preset2-patch.json。
nvngx_dlssnr.dll为已验证的15/15 O4修复版，SHA256 3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a。
nvngx_dlss.dll为原生SR运行库，不是旧71块NR模型。不要用其它原版Magpie.exe覆盖，否则会丢失Preset2固定。
自动更新关闭，以免后台更新覆盖此已核验EXE。

使用：以720p游戏窗口开始，保持前台，选择3秒后缩放；切换任务会按Magpie逻辑结束全屏缩放。
本路线不再有add-on的F6开关，比较请用Magpie自带效果/对比工具。
日志在logs/magpie.log，应出现Feature18、preset=fixed-2、style1、signed-snippet及evaluateGPU计时。

实测：同一3080 Laptop，720p动画窗口到4K，Feature18连续960次成功、0失败，NR GPU窗口均值15.868~16.199ms。
后级SR和同步也有成本，publication fence约21.1~21.5ms，动画窗口评估节奏约36FPS。
不能把1/16ms直接当成整机实际FPS，也不冒充已经验收光环40+FPS。
仅默认使用31块Small；外置71块旧模型和独立CUDA引擎不在本包。

本目录与正式ZIP均为原生路线B。替换前文件/ZIP和回退说明位于：
C:\DLSS5-5090-dll\backups\20261024-Magpie-native-release
所有文件SHA256见SHA256SUMS.txt。

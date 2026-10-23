DLSS5-AMD 0.15-900P · Magpie 版（2026-09-14）
============================
整包文件：Magpie-DLSS5-AMD-0.15-900P.zip

把 DLSS 5 的神经网络（DLSSNR）跑在 AMD RX 9070 XT（RDNA4）上，以 Magpie 窗口缩放器为载体：
支持宽不超过 1920、高不超过 1080 的普通游戏窗口，不需要游戏自己支持 FSR 或 DLSS。
窗口比 1080p 少几个像素也能用，小窗口自动按原宽高比适配。
本包固定用 1600x900 进行网络计算，建议游戏窗口设为 1600x900，再由 FSR4 放大到 2K/4K。
这是900p性能档；内部计算不会按帧率自动升降。
游戏窗口 -> FSR3（本插件的 DLSS5 入口）-> FSR4 放大到屏幕 -> XeSS 帧生成 -> 显示。
效果组里名叫 FSR3_SR 的那一项，就是本插件接入 DLSS5 的位置；界面名称仍是 FSR3，
不用另外添加 DLSS5 滤镜。第一项保持输入尺寸，后面的 FSR4 才负责放大。

本包内容
--------
  Magpie.exe 及其文件            Magpie 实验分支 0.6.6（SAOG0721/Magpie，GPL-3，许可见 LICENSE-Magpie.txt；A 卡用不到的 NVIDIA 运行库已去掉）
  config\config.json             Magpie 便携模式配置（预设好的效果组和选项）
  dxgi.dll                       ReShade 6.8 加载器（原版，未修改；放在 Magpie.exe 旁边就会被加载）
  dlss5-amd.addon64              本移植的 DLL（.addon64 是 ReShade 的扩展名，不要改名）
  DLSS5-D3D12-721\               微软 DirectX 12 Agility SDK 1.721 预览运行时，Shader Model 6.10 需要它
  DLSS5-AMD\                     权重、编译好的着色器、运行参数（必须和 dlss5-amd.addon64 在同一目录）
  SHA256SUMS.txt                 文件校验

需要
----
  1. RX 9070 / 9070 XT（RDNA4）+ AMD 26.10.07.02 预览驱动（正式驱动没有 Shader Model 6.10 的 wave matrix）。
     AMD 官方下载：https://drivers.amd.com/drivers/amd-software-adrenalin-edition-26.10.07.02-win11-rc7-agility-sdk.exe
     注意：Windows Update 会悄悄把预览驱动换成正式驱动（带在系统更新里），之后画面会写 "INIT FAILED"。
     重装预览驱动即可；要防再犯，组策略里禁止 Windows Update 带驱动（注册表
     HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate 建 DWORD ExcludeWUDriversInQualityUpdate=1）。
  1b. Windows 开发人员模式必须打开（设置 -> 系统 -> 开发者选项 -> 开发人员模式）。插件靠 D3D12EnableExperimentalFeatures
      打开实验性着色器模型，这个调用只在开发人员模式下成功；关着的话插件初始化就停在第一步，画面永远是 Magpie 自己的 FSR3。
      判断：DLSS5-AMD\logs\native-submission-order.txt 里 "sdk721_before_device ... experimental=" 后面不是 00000000 就是它。
      不需要装 SM 6.10 编译器、HIP、任何 SDK：着色器已经编好在包里。
  2. 本包已含 Magpie 实验分支（https://github.com/SAOG0721/Magpie）。
  3. 游戏选择窗口模式，宽不超过 1920、高不超过 1080；普通窗口和无边框窗口都可以。
     显示器可以是 2K、4K，包内 FSR4 默认充满屏幕；想保留原宽高比，可改成适应屏幕。
     若看到 "DLSS5-AMD: INPUT MAX 1920X1080 (NOW WxH)"，请减小游戏窗口，
     并确认效果组第一站 FSR3 没有提前放大。

安装（整包版：Magpie 本体已经在里面，解压即用）
----
  1. 解压到任意目录（路径别带中文），运行 Magpie.exe。便携配置随包，选择效果组 "DLSS5-AMD" 即可。
     已预设 FSR3_SR -> FSR4_SR -> XeSS_FrameGeneration_x2_ZeroMV。
     光流默认只在第一项 FSR3（DLSS5）开启 AMDOF；FSR4 和 XeSS 插帧的 Optical Flow Method 均选 None。
     关掉后两项的额外光流不会关闭放大或插帧。
     如果自己调整效果组：FSR3 的缩放选相对于输入尺寸、水平/垂直均 1 倍；
     FSR4 选充满屏幕。不要把 FSR3 设成适应屏幕。
     不需要插帧时，删掉最后的 XeSS_FrameGeneration_x2_ZeroMV 即可。
  2. 游戏选择窗口模式，建议1600x900；也接受不超过1920x1080的窗口，实际尺寸略小没关系。
  3. 回到游戏，按 Alt+Shift+A 激活缩放。初始化通常需要 3~5 秒，首次启动可能更久。
     左上角先显示 "DLSS5-AMD: INITIALIZING..."，接管后显示网络自己的 FPS 和耗时，数字至少每三秒刷新。
     若显示 "INIT FAILED - SEE DLSS5-AMD\LOGS"，检查开发人员模式和预览驱动。
     再按一次 Alt+Shift+A 停止缩放，可以对比原图。


已知
----
  - 用户实玩反馈：900p效果比720p更好，帧率较稳；1080p搭配插帧则不稳。
    独立合成源测试的900p推理约16.71ms/60fps，不含游戏、捕获、FSR4和帧生成开销。
    实际帧率随游戏和场景变化。左上角是网络帧率；Magpie 效能分析器的总帧率包含插帧。
  - 计算档位：native-game-flags.txt 中 DLSS5_NETWORK_HEIGHT=900（可改720/900/1080，完全退出并重启Magpie生效）。
  - 小窗口适配默认开启（DLSS5-AMD\native-game-flags.txt 中 DLSS5_FIT_INPUT=1），FPS 和 XeSS 帧生成也默认开启。
  - 输入是显示用的 8 位 sRGB 图（不是游戏内钩子那种线性 HDR 场景色）；插件按 sRGB 直通处理（DLSS5_CODEC_SRGB=1），
    亮度和原图一致。0.09 里暗部皮肤上偶尔闪的 8 像素方块在 0.10 修掉了（硬件 FP8 转换对超范围值不饱和、出 NaN，现在进矩阵前夹到 ±448）。
  - DLSS5（第一项 FSR3）的运动向量来自 Magpie 的光流估计（Optical Flow Method 选 AMDOF）；光流在平坦暗部会给出几万像素的垃圾向量，
    插件把超过 64 像素的向量当静止处理（DLSS5-AMD\native-game-flags.txt 的 DLSS5_MOTION_MAX_PX），否则会出现黑色/粉色的方块闪烁。
  - 强度：DLSS5-AMD\native-game-flags.txt 里加一行 DLSS5_STRENGTH=<细节>,<颜色>（各 0～1，默认 1,1 = 网络结果全用；
    0.5,1 就是细节一半原图一半、颜色修正全用）。这是 NVIDIA 面板里"强度"那个滑杆对应的两个混合系数；改完重启 Magpie 生效。
    风格预设没有：DLL 里的其他网络预设没有提取，本包只有捕获时那一套权重。
  - 停止缩放再激活，插件会重新接管（需要重新初始化）。
  - 日志：DLSS5-AMD\logs\native-game-oneshot.txt（初始化）、native-submission-order.txt（每帧观察）。
  - 屏幕提示不想要：DLSS5-AMD\native-game-flags.txt 里加一行 DLSS5_NOTICE=0；帧率不想看：删掉 DLSS5_SHOW_FPS=1。
  - F6 是本插件的开关键（全局）；如果同一台机器上游戏里也装了本插件的游戏版，两边会一起切。

卸载
----
  整个目录删掉即可，不写注册表、不碰 AppData。

来源
----
  https://github.com/lmxxf/dlss5-on-amd-9070xt-porting（源码、每个 tag 的改动、开发记录）

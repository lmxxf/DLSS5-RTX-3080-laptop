DLSS5-AMD 0.26 · Magpie 版（HIP 后端）
============================
整包文件：Magpie-DLSS5-AMD-0.26.zip

把 DLSS 5 的神经网络（DLSSNR）跑在 AMD RX 9070 XT（RDNA4）上，以 Magpie 窗口缩放器为载体：
支持宽不超过 1920、高不超过 1080 的普通游戏窗口，不需要游戏自己支持 FSR 或 DLSS。
本包按输入自动选择网络档位，建议游戏窗口设为 1600x900，再由 FSR4 放大到 2K/4K。
游戏窗口 -> FSR3（本插件的 DLSS5 入口）-> FSR4 放大到屏幕 -> XeSS 帧生成 -> 显示。
效果组里名叫 FSR3_SR 的那一项，就是本插件接入 DLSS5 的位置；界面名称仍是 FSR3，不用另外添加 DLSS5 滤镜。

0.26 更新
  - FFN直接读FP8字节片段，省去输入暂存和两道同步；C256权重预排为连续矩阵片段，减少分散读取和字节拼装。
  - 开启配套DLSS5_HIP_MH_FFN_FRAG256=1，保留gfx1200/gfx1201自动选择与原有缩放/插帧流水线。
  - 补齐共享R11G11B10解码shader，修复游戏版《匹诺曹》低效果品质黑屏；打包增加shader编译/绑定检查。
  - 计算优化已通过离线回归及《剑星》实玩；0.26 Magpie整包的画面和帧率待实测。

0.25 更新
  - 同一份源码编译 gfx1200 / gfx1201 两套内核，按实际显卡自动选择；优先通过 LUID 匹配设备。
    RX 9070系列已在本机验证；RX 9060/9060 XT已完成编译与包检查，运行效果待网友反馈。
  - 带上C32/MH指数复用、有界倒数、完整MH字节流、解码字节输出和完整tile快路径；修复900档解码尾部漏写。
  - HIP内核和权重改用Unicode路径读取，修复中文目录下HIP文件存在却提示找不到的问题。
  - Magpie仍走原有接入路径，DLSS5_PRE_UPSCALE=0；FSR3→FSR4→XeSS配置沿用0.23。
    配套DLL已编译、网络回归通过；0.25用户实测1080P只做DLSS5约37fps，与之前基本持平。

0.23 与 0.22 的区别
  - 修复带核显（AMD Radeon(TM) Graphics）或第二块显卡的机器上初始化失败（画面 INIT FAILED，日志 bridge currently requires exactly one HIP GPU）：
    插件按 Magpie 实际使用的显卡名字在 HIP 设备里选同名的那块；Magpie 的显卡选项请选 RX 9070 XT。单卡机器行为不变，内核、权重、输出与 0.22 逐位相同。

0.22 与 0.21 的区别
  - 900 档把 1600x900 补到 960 行而不是 1024 行（补边方式和 1080 档一致），同样的内核少算约 6%：网络每帧约 15.2 → 14.4ms，900 窗口大约 +3 帧。
    输出和 0.21 不逐位相同（补边内容经 ViT 全局注意力影响整幅，两种补法都没有对错），肉眼看不出差别；要 0.21 的布局把 DLSS5_NETWORK_HEIGHT 写成 900w。
  - 720/1080 档、内核、权重与 0.21 相同。

0.21 与 0.20 的区别
  - 网络档位自动选择（DLSS5_NETWORK_HEIGHT=auto）：窗口不超过 1280x720 用 720 档、不超过 1600x900 用 900 档、其余用 1080 档（上限仍是 1920x1080）；
    左上角帧率数字后面显示实际档位，如 1600X900。
  - 说明文案：显存实测 1.2GB（不是 3GB）；正式版驱动已有用户反馈可用；新增性能档说明（见"已知"）。
  - 内核、权重、输出与 0.20 逐位相同。

0.20 与 0.15 的区别
--------
  推理后端从 DirectX 12 Shader Model 6.10 换成了 AMD HIP：网络的 24 个内核以 GPU 原生二进制（.hsaco）随包提供，
  由显卡驱动自带的 HIP 运行时执行，输出与 0.15 逐位相同（同一输入、同一种子、同一历史帧，40 帧输出哈希完全一致）。
  因此不再需要：预览驱动的 Shader Model 6.10、DirectX Agility SDK 1.721 预览运行时、Windows 开发人员模式。
  速度：独立测试台 1600x900 每帧约 15.5ms（0.15 为 16.8ms）；《剑星》游戏内 900p 实测约 52 fps（0.15 约 47）。
  上述为历史版本结果，不能代替0.26的实测。

本包内容
--------
  Magpie.exe 及其文件            Magpie 实验分支 0.6.6（SAOG0721/Magpie，GPL-3，许可见 LICENSE-Magpie.txt；A 卡用不到的 NVIDIA 运行库已去掉）
  config\config.json             Magpie 便携模式配置（预设好的效果组和选项）
  dxgi.dll                       ReShade 6.8 加载器（原版，未修改；放在 Magpie.exe 旁边就会被加载）
  dlss5-amd.addon64              本移植的 DLL（.addon64 是 ReShade 的扩展名，不要改名）
  DLSS5-AMD\                     权重、HIP 内核（native-game-tiled-assets\HIP\ 下两个架构目录，各24个 .hsaco）、运行参数（必须和 dlss5-amd.addon64 在同一目录）
  SHA256SUMS.txt                 文件校验

需要
----
  1. RX 9070 / 9070 XT（gfx1201），或 RX 9060 / 9060 XT（gfx1200，待实机反馈）。RX 7000 不支持。
  2. 显卡驱动带 HIP 7 运行时：C:\Windows\System32\amdhip64_7.dll 存在即可。
     作者在 AMD 预览驱动 32.0.31007.2048（0.15 要求的那个）上验证；正式版驱动同样带这个文件，已有用户反馈正式版可用。
     初始化失败时看 DLSS5-AMD\logs\native-game-oneshot.txt 里 HIP 相关的行，以及 native-hip-device.txt 里的架构和模块路径。
     不再需要开发人员模式，不需要装 HIP SDK、SM 6.10 编译器或任何 SDK。
  3. 游戏选择窗口模式，宽不超过 1920、高不超过 1080；普通窗口和无边框窗口都可以。
     若看到 "DLSS5-AMD: INPUT MAX 1920X1080 (NOW WxH)"，请减小游戏窗口，并确认效果组第一站 FSR3 没有提前放大。

安装（整包版：Magpie 本体已经在里面，解压即用）
----
  1. 完整解压到独立目录，运行 Magpie.exe。便携配置随包，选择效果组 "DLSS5-AMD" 即可。
     已预设 FSR3_SR -> FSR4_SR -> XeSS_FrameGeneration_x2_ZeroMV。
     光流默认只在第一项 FSR3（DLSS5）开启 AMDOF；FSR4 和 XeSS 插帧的 Optical Flow Method 均选 None。
     如果自己调整效果组：FSR3 的缩放选相对于输入尺寸、水平/垂直均 1 倍；FSR4 选充满屏幕。不要把 FSR3 设成适应屏幕。
     不需要插帧时，删掉最后的 XeSS_FrameGeneration_x2_ZeroMV 即可。
  2. 游戏选择窗口模式，建议 1600x900；也接受不超过 1920x1080 的窗口，实际尺寸略小没关系。
  3. 回到游戏，按 Alt+Shift+A 激活缩放。初始化通常需要 3～5 秒。
     左上角先显示 "DLSS5-AMD: INITIALIZING..."，接管后显示网络自己的 FPS 和耗时。
     若显示 "INIT FAILED - SEE DLSS5-AMD\LOGS"，先确认 System32 里有 amdhip64_7.dll。
     再按一次 Alt+Shift+A 停止缩放，可以对比原图。
  从 0.22/0.21/0.20/0.15 升级：直接换整个目录；旧包的 DLSS5-D3D12-721 和 enable-game-sdk721.txt 在 0.20 起没有了，属正常。

已知
----
  - 计算档位：配置里 DLSS5_NETWORK_HEIGHT=auto——按窗口自动选档：宽高不超过 1280x720 用 720 档，不超过 1600x900 用 900 档，其余（最大 1920x1080）用 1080 档；
    比档位小的窗口按比例贴进画布。也可写死 720/900/1080。左上角帧率数字后面显示网络实际计算的分辨率（如 1600X900）。完全退出并重启 Magpie 生效。
  - 小窗口适配默认开启（DLSS5_FIT_INPUT=1），FPS 和 XeSS 帧生成也默认开启。
  - 输入是显示用的 8 位 sRGB 图；插件按 sRGB 直通处理（DLSS5_CODEC_SRGB=1），亮度和原图一致。
  - DLSS5（第一项 FSR3）的运动向量来自 Magpie 的光流估计（AMDOF）；超过 64 像素的向量当静止处理（DLSS5_MOTION_MAX_PX）。
  - 强度：配置里加一行 DLSS5_STRENGTH=<细节>,<颜色>（各 0～1，默认 1,1）。改完重启 Magpie 生效。
  - 默认输出：全 71 块 + 快速数值（DLSS5_SKIP_BLOCKS= 留空、DLSS5_FAST_NUMERIC=1，对 NVIDIA 原版 47.55 dB、无整体偏色；个人改动写进 custom-config.txt）。
  - 跳块提速（可选，有损）：custom-config.txt 里写 DLSS5_SKIP_BLOCKS=42,43,46，每帧快约 0.20/0.32ms（900/1080），对 NVIDIA 原版约掉 3.3 dB、有整体偏色；删掉该行恢复默认。
    性能档（跳 9 块）：DLSS5_SKIP_BLOCKS=12,28,41,42,43,44,46,52,53，网络每帧再快约 0.8ms（900p 15.25 → 14.48ms，约 5%），
    代价是相对默认输出 PSNR 约 30dB（细节、暗部有可见差别）。
  - 叠层（可选）：DLSS5_MULTI_PASS=1/2/3（默认 1）把网络输出再跑 1～2 遍，风格更浓、耗时约 N 倍；按 F9 在 1→2→3 间轮换
    （DLSS5_MULTI_PASS_HOTKEY 改键，0 关闭），选择写进 custom-config.txt。
  - 配置分三层：default-config.txt → custom-config.txt → 旧安装遗留的 native-game-flags.txt，后面的盖前面的；系统环境变量最高；
    同一文件里同一项写两次取最后一行；值留空（KEY=）表示用程序内置默认。
  - 停止缩放再激活，插件会重新接管（需要重新初始化）。
  - 日志：DLSS5-AMD\logs\native-game-oneshot.txt（初始化）、native-submission-order.txt（每帧观察）。
  - 屏幕提示不想要：加一行 DLSS5_NOTICE=0；帧率数字不想看：设 DLSS5_SHOW_FPS=0；整行文字（含分辨率）不想看：设 DLSS5_NOTICE=0。修改后完全退出并重启Magpie。
  - F6 是本插件的开关键（全局）；如果同一台机器上游戏里也装了本插件的游戏版，两边会一起切。

卸载
----
  整个目录删掉即可，不写注册表、不碰 AppData。

来源
----
  https://github.com/lmxxf/dlss5-on-amd-9070xt-porting（源码、每个 tag 的改动、开发记录）

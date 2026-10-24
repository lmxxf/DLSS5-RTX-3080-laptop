《剑星》(Stellar Blade) DLSS 5 网络 AMD 移植 —— 用户运行包 0.23（HIP 后端）

这是把 DLSS 5（DLSSNR）的神经网络逐块移植到 AMD 显卡上的实验版本，不是 NVIDIA、AMD 或游戏厂商的官方产品。
源码与开发记录：https://github.com/lmxxf/dlss5-on-amd-9070xt-porting
公众号系列（中文）：微信搜索合集「DLSS5」

0.23 与 0.22 的区别
  - 修复带核显（AMD Radeon(TM) Graphics）或第二块显卡的机器上初始化失败（画面 INIT FAILED，日志 bridge currently requires exactly one HIP GPU）：
    插件现在按游戏实际使用的显卡名字在 HIP 设备里选同名的那块，单卡机器行为不变。内核、权重、输出与 0.22 逐位相同。

0.22 与 0.21 的区别
  - 900 档补边 1024 → 960 行（补法同 1080 档），同样的内核少算约 6%（网络 15.2 → 14.4ms，1600x900 窗口约 +3 帧）。输出与 0.21 不逐位相同但肉眼无差别；
    要 0.21 的布局把 native-game-flags.txt 里 DLSS5_NETWORK_HEIGHT 改成 900w。内核、权重与 0.21 相同。

0.21 与 0.20 的区别
  - 网络档位自动选择（DLSS5_NETWORK_HEIGHT=auto，1600x900 窗口即 900 档），左上角帧率后面显示实际档位。
  - 说明文案：显存实测 1.2GB；正式版驱动已有用户反馈可用；新增性能档说明。内核、权重、输出与 0.20 逐位相同。

0.20 与之前版本的区别
  推理后端从 DirectX 12 Shader Model 6.10（wave matrix）换成了 AMD HIP：网络的 24 个内核以 GPU 原生二进制（.hsaco）随包提供，
  由显卡驱动自带的 HIP 运行时执行，输出与 0.15 的 DX12 版逐位相同（同一输入、同一种子、同一历史帧，40 帧输出哈希完全一致）。
  因此不再需要：预览驱动的 Shader Model 6.10、DirectX Agility SDK 1.721 预览运行时、Windows 开发人员模式。
  速度：独立测试台 1600x900 每帧约 15.5ms（0.15 的 DX12 版 16.8ms）；游戏内 900p 实测约 52 fps（0.15 约 47）。

已测试环境
  Windows 11、AMD Radeon RX 9070 XT、AMD 驱动 32.0.31007.2048、《剑星》Steam 版、1600x900 窗口、FSR 质量档。
  其他显卡、分辨率、HDR 尚未验证；RX 7000 系列不支持（内核用了 RDNA4 的 FP8 矩阵指令，只编了 gfx1201）。

必须先满足的条件
  1. 显卡驱动带 HIP 7 运行时：C:\Windows\System32\amdhip64_7.dll 存在即可。
     作者在 AMD 预览驱动 32.0.31007.2048（0.15 要求的那个）上验证；正式版驱动同样带这个文件，已有用户反馈正式版可用。
     若初始化失败请看 DLSS5-AMD\logs\native-game-oneshot.txt 里 HIP 相关的行并反馈。
  2. 显存 16GB。插件实测占 1.2GB（900p：权重 0.6GB + 激活 0.3GB + 共享缓冲 0.07GB + 运行时开销，见 logs\native-hip.txt 的 hip_memory 行）。
     《星刃》贴图「非常高」加上这 1.2GB 会把 16GB 顶满，帧率掉到 25 以下不恢复，**贴图质量建议「高」或更低**。

包内文件
  d3d12.dll                          ReShade 6.8 加载器（原版，未修改）
  dlss5-amd.addon64                  本移植的 DLL（.addon64 是 ReShade 的扩展名，不要改名）
  DLSS5-AMD\                         网络权重、HIP 内核、运行参数和日志目录（约 600MB）
    default-config.txt                 默认配置，一行一个开关；升级会被覆盖，不要改它
    custom-config.template.txt         个人配置模板：复制一份改名为 custom-config.txt，只写想改的那几行
    native-game-tiled-assets\          权重（.f16/.f32）、少量运行时着色器（.hlsl）、噪声表（noise.f32）
      HIP\                             24 个 gfx1201 HIP 内核（.hsaco），必须在这个位置
    logs\                              运行日志写在这里
  ReShade-LICENSE.txt / MinHook-LICENSE.txt   第三方组件的许可
  SHA256SUMS.txt                     所有文件的校验和

安装
  1. 完全退出游戏。
  2. Steam → 剑星 → 管理 → 浏览本地文件，进入 SB\Binaries\Win64。
  3. 如果该目录已有 d3d12.dll 或其他 ReShade/mod 加载器，先备份；不要在不了解的配置上直接覆盖。
     从 0.15 升级：删掉旧的 DLSS5-D3D12-721 文件夹和 DLSS5-AMD\enable-game-sdk721.txt（HIP 版不用它们），其余直接覆盖。
  4. 把本包里的全部内容（两个文件 + 一个文件夹）复制进 Win64。DLSS5-AMD 文件夹必须和 dlss5-amd.addon64 在同一目录。
  5. 游戏设置：窗口 1600x900、AMD FSR 超分辨率（质量档）。默认配置里 DLSS5_NETWORK_HEIGHT=auto 按窗口自动选档（≤1280x720 用 720，≤1600x900 用 900，其余用 1080），1600x900 窗口即 900 档；左上角帧率后面显示实际档位。
  6. 从 Steam 正常启动。主菜单里不会有任何变化——网络只在 3D 场景开始渲染（读档之后）时接管 FSR 的超分步骤，
     第一次接管要读权重、装载内核，约 3～5 秒，这段时间画面是原生 FSR，之后自动切换。

怎么确认它在工作
  左上角显示网络自己的 FPS 和每帧耗时（DLSS5_SHOW_FPS=1）；F6 循环切换：神经网络输出 / 原生 FSR 画面 / 左右对照。
  日志：DLSS5-AMD\logs\native-game-oneshot.txt 和 native-submission-order.txt。
  如果一直是原生画面，先确认 System32 里有 amdhip64_7.dll，再看 oneshot 日志里 HIP 初始化的错误行。

已知问题
  1. 换区、过场动画后帧率可能掉几秒，多数情况 5～30 秒内恢复；这是显存被游戏贴图挤到系统内存造成的，
     降低贴图质量或在游戏的 Engine.ini 里加 [SystemSettings] r.Streaming.PoolSize=6000 能缓解。
  2. 默认输出：全 71 块 + 快速数值（DLSS5_SKIP_BLOCKS= 留空、DLSS5_FAST_NUMERIC=1，对 NVIDIA 原版 47.55 dB、无整体偏色）。
     可选提速（有损）：custom-config.txt 里写 DLSS5_SKIP_BLOCKS=42,43,46，每帧快约 0.20/0.32ms（900/1080），
     对 NVIDIA 原版约掉 3.3 dB、有整体偏色；删掉该行恢复默认。
     性能档（可选，跳 9 块）：DLSS5_SKIP_BLOCKS=12,28,41,42,43,44,46,52,53，网络每帧再快约 0.8ms（900p 15.25 → 14.48ms，约 5%），
     代价是相对默认输出 PSNR 约 30dB（细节、暗部会有可见差别）。
  3. 叠层（可选）：DLSS5_MULTI_PASS=1/2/3（默认 1）把网络输出再跑 1～2 遍，风格更浓、耗时约 N 倍；游戏里按 F9 在 1→2→3 间轮换
     （DLSS5_MULTI_PASS_HOTKEY 改键，0 关闭），选择写进 custom-config.txt。
  4. 配置分三层：default-config.txt → custom-config.txt → 旧安装遗留的 native-game-flags.txt，后面的盖前面的；系统环境变量最高；
     同一文件里同一项写两次取最后一行；值留空（KEY=）表示用程序内置默认。
  5. 只在 1600x900 + FSR 质量档上验证过。
  6. 与其他 ReShade 插件、帧生成、HDR 的组合未测试。

卸载
  退出游戏后删除 d3d12.dll、dlss5-amd.addon64、DLSS5-AMD 三项，恢复自己备份的文件。
  游戏更新或换版本后需要重新验证。

问题与更新：https://github.com/lmxxf/dlss5-on-amd-9070xt-porting

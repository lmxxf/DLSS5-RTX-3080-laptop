# Onimusha Phase 10 独立CUDA Runtime部署回执

游戏目录：`C:\XboxGames\Onimusha- Way of the Sword\Content\`。已部署，未启动游戏；画质/游戏帧率由Zero实机验收。

- Linux 3 warmup/5 iter快验：896×512 median7.999ms、1280×768 median14.092ms；均Small31、Style1、Graph off、invalid0、first/last bitdiff0，32种活跃核，无对齐错误。这不是此前50/80性能表的新替代值。
- C256默认门控现为所有TierGeometry/free_geometry融合，只有`DLSS5_LAB_C256_SPLIT=1`显式退回分散路径。
- `build-runtime.sh`交叉编译当前Host和Ampere预洗牌CPU权重打包。Runtime模块探测增加sm_86；flags loader接受CUDA架构、AMPERE_WEIGHTS和C256_SPLIT配置，避免路径识别漏掉优化核。
- `LmxxfNrRuntime.dll`：5,048,942 B，SHA256 `ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353`。
- 从指定0.44底包提取DLSS5-AMD、D3D12_Optiscaler、shaders共667个文件，内容解压后逐个SHA核对；含93个Small权重、207个cso。
- `HIP/sm_86`中40个Phase10 selected hsaco逐个与冻结manifest相符，AMPERE_WEIGHTS_V2标记一致；HIP根/子目录SHA256SUMS更新。gfx1200/gfx1201已移除，HIP根无其它hsaco。
- 原INI、PTX wrapper与模型DLL已备份并核对SHA，游戏根两个旧NR DLL移除；dxgi.dll、dinput8.dll保持原文件。
- INI：Enabled=true、NrBackend=lmxxf、WhitePointSource=1、Preset=2、Style=1、Dx12Upscaler=dlss。
- default-config：MULTI_PASS=0.5、FAST_NUMERIC=1、AMPERE_WEIGHTS=1、CUDA_ARCH_NAME=sm_86、C256_SPLIT=0、NETWORK_FREE_RES=1、STYLE=1、HIP_GRAPH=0。

特别修正：底包FREE_RES原为0，854×480会先套720档并跑1344×768。改为1后，Windows真实D3D12/CUDA探针的PrepareFrame成功，报告`net=854x480 color_job=854x480 proc=896x512 modules_ok=40 hip=1`；wave-owned、C512、ViT gates为1，architecture=sm_86。API/Create/PrepareSession/PrepareFrame/Cancel全status0。日志：windows-probe-free.log。

备份：`C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0\`。恢复其中OptiScaler.ini、nvngx.dll_dlssnr.dll、nvngx_dlssnr.dll到Content即可恢复原PTX选择；旧INI会切回nvidia backend。部署完整哈希/原文件回执为该目录下phase10-deployment.json及backup-manifest.json。

当前游戏配置载入的模型是31块Small。底包其余公共资产按用户指定完整解压，未将本次游戏配置改动同步到其它游戏或发布ZIP。

# Phase15 输入证据与性能暂停条件

起点9c27a1c/830185d，工作树干净。唯一正确性/性能基线为Phase14 selected和新720 F32 gold，900/1080旧gold不改。

发现一张有Microsoft GameDVR与sRGB元数据的《明末：渊虚之羽》1920×1080 RGBA PNG，已查看确认是武器菜单。SHA `a055f4e3e43ee2094ca76433b8c57587e35eb5a73a6013622f540a5d52d1d29a`。它可用于真实来源SDR输入回归，但不是RE Engine原始线性HDR、不是独立动态游戏场景序列，也不能单凭它验收整体实机画质。文件仅读取，不改Windows目录。

旧文档确实引用1296×720 RGBA16F真实HDR捕获 `D:\DLSSNR-Lab\hip-backend\live-menu-before.f16`，本机没有D盘挂载及该文件。仓库/所有已有artifacts、dlss5-assets非权重文件、DLSS5 Windows实验目录与底包zip目录清单、Steam截图与GameDVR目录也没有找到可用原始HDR捕获。

两个看似帧输入的文件经数据核查：Temp/dlss5_frame_test/input.f16全RGBA为0，不能当真实图；发布验证记录/magpie-smoke-input.f16是0.15～0.80平滑人工渐变，不是游戏帧。原始路径、尺寸、SHA及统计在input-audit.json。旧“actual QKV”是实际网络执行捕获，来自合成benchmark输入，不是游戏帧QKV。

后续回归会使用该SDR截图、明确标注的整幅动态衍生帧和既有codec fixture生成器，并做普通白点1/HDR白点512的配对。由SDR线性化再乘512得到的输入只能叫**模拟HDR配对**，不能伪称原始HDR捕获。CPU按已有shader公式生成编码工作输入，不能声称已验证D3D12 shader/真实游戏HDR合成。

按用户“真实输入不足或发现新正确性问题，先提交证据并暂停性能侧”条件，**本轮暂停新的C32性能实验**。继续完成长期回归、动态/geometry/质量门和全模块重编加载，不以单一图案或43.58dB冒充旧45dB门槛。不要求Zero重新进游戏，不改游戏/Magpie/共享assets/发布包，不push、不部署。先记录证据，再按回归结果报告可用范围。

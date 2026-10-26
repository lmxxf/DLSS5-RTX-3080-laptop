# v0.2.0 正式部署与三包回执（2026-10-26）

已按WorkingPlan第3节1～4步执行。三个包统一PTX V2.1 hot255 /31块Small /Preset2 /Style1，15/15 O4原槽位。模型GPU median为 **720p6.66ms /900p9.70ms /1080p12.78ms**；完整正反实验见../../v21/final-results.md。V2.1相对V2严格0bit。

## 正式ZIP

目录：`C:\DLSS5-5090-dll\发布打包\`（已上传至 Gofile 镜像：`https://gofile.io/d/OOeOcxn6`）；每包有`.sha256`，`SHA256SUMS.txt`仅列本版三包。全部ZIP CRC、逐文件SHA及核心DLL哈希已核验。旧0.1.0 ZIP和清单归档在`archive/v0.1.0/`。Zero 实机验证：《鬼武者：剑之道》2K 性能档从 30 FPS 升至 **43 FPS**，《剑星》2K 性能档达**接近 60 FPS**。

| ZIP | 字节数 | SHA256 |
|---|---:|---|
|OptiScaler-REFramework-DLSS5-RTX30-0.2.0.zip|375533391|`531179b60d55e7147262e488afa760f8fc6422b353882ee5b223c47db3022d94`|
|OptiScaler-DLSS5-RTX30-0.2.0.zip|318461731|`ce7c18e05e286f17b93ee841d2ea9ae829f62cb0a5b3018b93500d3eb902509f`|
|Magpie-DLSS5-RTX30-0.2.0.zip|323386599|`e88a6c86ee6803de64cf6cabb1d3d2af3ef37565c91822a77a5dd8a6ef347739`|

共用核心`nvngx_dlssnr.dll`：266414592B，SHA **c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed**。包内不含路线A外置权重、HIP模块或LmxxfNrRuntime；Magpie继续使用Preset2补丁版exe（SHA b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea）。

## 本机同步

- 主`nvngx_dlssnr_sm86_fast.dll`与manifest已更新，v21/v2原副本保留。
- 鬼武者`C:\XboxGames\Onimusha- Way of the Sword\Content\`根与`_storage_`：恢复原版dxgi（aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2），恢复0x2b549的`75 03`，撤销AMD厂商入口热补丁。PTX原INI恢复，NrBackend=nvidia、WhitePointSource1、Preset2、Style1；转发桥SHA4f088f382171b3b3af4e2b34cb71b162788c947a55eeefc6e81e36206c59a0c9。两处NR均为V2.1；配套FFX/XeSS等库已补齐；DLSS5-AMD、LmxxfNrRuntime、add-on及旧shader移入备份，递归无活动路线A残留。
- 剑星`C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64\`：NR更新V2.1；默认TransferStrength/ColourStrength为 **1.0/1.0**；`OptiScaler-增强风格.ini`为1.5/1.1。常规ZIP同样配置。减小运动遮罩回退时增强图与原图的反差；没有把配置调整写成本轮实玩已证明闪烁消失。
- Magpie原目录升级为`发布打包\Magpie-DLSS5-RTX30-0.2.0\`，NR已替换，原Preset2补丁和用户config保留。
- Live校验清单、元数据、剑星原全量安装/恢复manifest已更新；旧OptiScaler日志归档，避免下一次把Phase10日志当成当前路径证据。

备份：`C:\DLSS5-5090-dll\backups\20261026-v020\`。`before.json`记录首次覆盖前文件，`onimusha-package-before.json`记录补齐包文件前的冲突，`route-a-removed/`保留原HIP路线目录，日志、原INI和旧生产DLL均保留；未覆盖更早的Onimusha-ptx-0.1.0备份。

## Windows验证与签名范围

三包实际内容均完成Windows D3D12/NGX Feature18加载、创建和5帧测量，全部nonfinite0；两套OptiScaler另外跑FFX loader/FFX→NGX→NR端到端，Host记录composition、detail1.00/colour1.00。所有烟测文件在打包前移出，包内容逐文件SHA与已测试内容对应。

Windows Get-FileHash确认三处最终部署NR均为c7d4c8b6…；驱动`_nvngx.dll` Authenticode为**Valid**。经过修改并移除失效证书表的NR DLL为**NotSigned**，这是预期状态；不能把SHA和NGX调用检查称为NVIDIA数字签名有效。记录分别在windows-signatures.json、windows-signatures-live.json、smoke-results.json。

没有启动游戏重测FPS/脸部观感，也没有启动Magpie重做捕获链；本轮是部署、配置、ZIP完整性与Windows API smoke验收。旧游戏/窗口FPS在公开文档中标为历史。

## 技术与性能说明

偶奇K16去掉MMA操作数准备中的跨lane SHFL；mapped保留5410/7632 PRMT。FB00/03/04/05/06 maxnreg255，FB01/02不变。其中FB00/03/06的STACK清零，FB04/05仍有80/8B最大STACK，不能写成全网零spill；详细资源表在v21。

0.1.0历史耗时15.83/24.47/32.04与本版6.66/9.70/12.78的比值约2.38/2.52/2.51×。上游O1历史37.13/49.89/67.69对应5.58/5.14/5.30×；900p不是5.3×。历史比值不是本轮同输入/等频对照；本轮不再为打包重复性能实验。

## 脚本与证据

`stage_deploy.py`为一次性、拒绝覆盖已有备份的部署入口；`smoke.py`执行包内容API验证；`package.py`复制未变ZIP压缩条目、重压V2.1和元数据，并核验CRC/逐文件SHA后归档旧包。`finalize_deployment.py`补齐鬼武者配套库、更新Live和恢复清单；`release_check.py`核对最终ZIP与配置。原始stage路径已在清理后删除；重做完整打包需先从archive/v0.1.0准备源，不要直接重复部署入口覆盖已完成现场。

smoke工具由仓内既有ffx_nr_smoke.cpp/ffx_loader_smoke.cpp重建，GPUOpen官方SDK头文件URL/SHA与工具链保存在smoke-toolchain.json，工具留在`C:\DLSS5-5090-dll\release-v020-tools\`。临时stage与RGB在验证后清理，旧ZIP/部署备份保留。Git只提交源码、日志、JSON和文档，不含DLL/ZIP，不push。

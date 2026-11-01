# RTX30 v0.4.0 本机正式发布回执

**状态：五处已部署、正式三包已生成并验证；本轮未上传网盘、未push。** 核心PTX V4.0 / `joint_up_cfg_pack4_fb2356`，266,414,592 B，15/15原槽位O4。

`749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`

[完整改进与使用说明](../../../doc/使用说明0.4.0.md) · [验证JSON](validation.json) · [ZIP清单](packages.json)

## 部署与回滚

五处核心均为同SHA：

- `C:/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll`
- `C:/XboxGames/Onimusha- Way of the Sword/Content/nvngx_dlssnr.dll`
- `C:/XboxGames/Onimusha- Way of the Sword/Content/_storage_/nvngx_dlssnr.dll`
- `C:/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64/nvngx_dlssnr.dll`
- `C:/DLSS5-5090-dll/发布打包/Magpie-DLSS5-RTX30-0.4.0/nvngx_dlssnr.dll`

Magpie原0.3.0目录重命名为0.4.0，配置/程序保持原字节。旧元数据与一份可回滚的v0.3.0核心保留在 `C:/DLSS5-5090-dll/backups/20261101-v040/`；游戏宿主、桥和INI的before/after散列见[现场凭据](live.json)。主旧原版输入、V3.1/V3.8/V4.0封存DLL未改。

## 三包与旧版归档

|ZIP|大小 B|SHA256|
|---|---:|---|
|`OptiScaler-REFramework-DLSS5-RTX30-0.4.0.zip`|375,010,382|`fefeff4e1bfdd5ddb218dd41e91671171748cb9bbd86bcde93c01bc20347ed4e`|
|`OptiScaler-DLSS5-RTX30-0.4.0.zip`|317,938,717|`751c75a1c71ab4077fcf058f32420ec9757267f4b5ca68747d2be11fd53c0870`|
|`Magpie-DLSS5-RTX30-0.4.0.zip`|322,863,632|`2a90d6b9c901952a40cfe86475e1727064b174f04b5bf3bbf39c0d1a80b6a901`|

ZIP位于 `C:/DLSS5-5090-dll/发布打包/`，逐包sidecar及顶层SHA清单已更新。旧0.3.0 ZIP、sidecar、清单、README和release JSON在 `archive/v0.3.0/` 逐字节归档；原v0.1.0/v0.2.0归档不动。复用未改成员的压缩数据并重新检查CRC及所有成员SHA；对应[归档凭据](archive.json)。

## 三项核心增量与度量

V3.8的FB456正零500处；34入口稳定32位源UP-Pair1288处、删除644拆分；FB2356经验Pack4（HMUL2.abs/LEA/LOP3/PRMT四核心）。相对v0.3.0静态非NOP152076→145461、PRMT19861→18781、STL/LDL107/108→99/100。

V4.0两轮配对进程median均值为720p5.61150/5.65975ms、900p8.26625/8.30000ms、1080p10.99500/10.98675ms；非游戏FPS或逐帧上界。27次所测输出对V3.8为0bit；经验Pack4仍不作为任意输入有界证明。配置默认1.0/1.0、增强1.5/1.1逐字节继承0.3.0。

## 五项Windows验证与完整性

- 三包各一次原生NGX Feature18 load/create/evaluate；
- 两个OptiScaler包各一次FFX loader及实际FFX→NGX→NR before-SR composition；
- 五项测试均returncode0/nonfinite0，组合日志有primary feature ready、FFX input和detail/colour1.00证据；
- 三ZIP CRC、内部全成员SHA、smoke后staging逐文件SHA通过；13个Windows Get-FileHash校验通过；patched NR为NotSigned，已安装NVIDIA驱动NGX core为Valid；
- 支持DLL/INI/Magpie.exe等非核心非元数据文件与0.3.0完全一致，五处现场支持文件也保持原值。

[原生测试完整输出](smoke-results.json)、[Windows哈希/签名](windows-signatures.json)、[执行记录](execution.json)。执行记录保留了一次verify脚本尚未落盘的调度失败；补齐后最终完整校验通过，五项API测试本身均成功。没有伪装成游戏实玩或新FPS测试。

## 清理与复现脚本

`prepare.py`→`install.py`→`package.py`→`smoke.py`→`windows_check.py`→`verify.py`→`cleanup.py`，由common.run聚合stdout/stderr进JSON。流程按版本守卫路径，避免覆盖已存在的正式ZIP或回滚备份。

staging、测试工具和rgb32帧已删除，宿主临时日志在每次测试后捕获并移除，无单次.log碎文件；回滚备份、三包和版本归档保留。[清理凭据](cleanup.json)。正式ZIP与核心不提交Git；公开上传状态仍为待上传。

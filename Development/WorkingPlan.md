# WorkingPlan — v0.4.0 正式版发布：本机五处部署（《剑星》《鬼武者》等）与三个正式 ZIP 打包验证（2026-11-01 11:08）

## 0. 发布基准与小颗粒度 Git 提交纪律

1. **`v0.4.0` 核心二进制基准**：
   - 采用经 12 轮搜索闭环与终审批准（[《0536 审核意见》](doc/性能评估20261101-0536-审核意见.md)）的最终胜出版本 **`PTX V4.0` (`joint_up_cfg_pack4_fb2356`)**：
     - 源路径：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`
     - 文件大小：`266,414,592 B`（15/15 原 PE 槽位满血 `O4`）
     - SHA256：`749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`
     - 核心指标：38 活跃 FP8 核非 NOP 静态 SASS 降至 **`145,461` 条**（相比 `v0.3.0 / V3.1_pack5` 的 `152,076` 条净减 `6,615` 条 / `-4.35%`，`PRMT` 净减 `1,080` 条至 `18,781`，`STL/LDL` 从 `107/108` 压降至 `99/100`）；同轮正反 ABBA 配对均值 **720p `5.61~5.66 ms`、900p `8.27~8.30 ms`、1080p `10.99~11.00 ms`**（首次压入 11ms 以内，所测 27 次三档输出检查相对 `V3.8` / `v0.3.0` 全部 `0 bit-diff`）。
2. **⚠️ 最小颗粒度 Git 提交铁律（必须严格执行）**：
   - 拆分为 3 个干净的小颗粒度 `git commit`（严禁加 `Co-Authored-By`，不 push）：
     - Commit 1：`Development/ptx-patcher/release-rtx30/v040/` 打包、本机五处部署与 Windows Smoke 验证脚本及 JSON 凭据（不含单次 `.log` 碎文件）；
     - Commit 2：新增 `Development/doc/使用说明0.4.0.md` 并更新 `Development/ptx-patcher/release-rtx30/v040/README.md`、`Development/doc/使用说明.md`；
     - Commit 3：同步更新根目录 `README.zh-CN.md`、`README.md`、`CHANGELOG.zh-CN.md`、`CHANGELOG.md`、`Development/ptx-patcher/README.md`、`Development/DevHistory.md` 与 `Development/WorkingPlan.md`。

---

## 1. 本轮派单任务（`v0.4.0` 本机游戏部署与正式三包构建，由闇执行）

请参考 `Development/ptx-patcher/release-rtx30/v030/` 的成熟流程，在 `Development/ptx-patcher/release-rtx30/v040/` 下完成以下步骤：

### 步骤 1：本机 5 处运行位置同步更新为 `PTX V4.0`（`v0.4.0`）并备份旧现场
1. 先将当前本机 `v0.3.0` 的相关元数据备份至 `/mnt/c/DLSS5-5090-dll/backups/20261101-v040/`；
2. 将 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`（SHA256 `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`）同步覆盖安装至本机全部 5 个运行位置并逐一校验 SHA256（保持各游戏目录原有的 `dxgi.dll`、`dinput8.dll`、转发桥与 `OptiScaler.ini` 配置不变）：
   - ① `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll`
   - ② **《鬼武者：剑之道》根目录**：`/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/nvngx_dlssnr.dll`
   - ③ **《鬼武者：剑之道》镜像目录**：`/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/_storage_/nvngx_dlssnr.dll`
   - ④ **《剑星》（Stellar Blade）**：`/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64/nvngx_dlssnr.dll`
   - ⑤ **Magpie 目录**：将 `/mnt/c/DLSS5-5090-dll/发布打包/Magpie-DLSS5-RTX30-0.3.0` 更新/重命名为 `Magpie-DLSS5-RTX30-0.4.0`，替换其中的 `nvngx_dlssnr.dll` 并同步包内版本说明与校验清单。

### 步骤 2：构建 `v0.4.0` 三个正式发布 ZIP 包与旧版归档
1. 将 `/mnt/c/DLSS5-5090-dll/发布打包/` 下现有的三个 `0.3.0` ZIP、`.sha256` 及清单移入 `/mnt/c/DLSS5-5090-dll/发布打包/archive/v0.3.0/` 归档保存（保留 `archive/v0.1.0` 与 `archive/v0.2.0` 不动）；
2. 基于 `0.3.0` 正式包结构制作三个 `0.4.0` 正式包（仅替换核心 `nvngx_dlssnr.dll` 为 `V4.0` 并更新包内 `README` / 版本号 / `SHA256SUMS.txt` 清单，其余宿主 DLL、`Magpie.exe`、默认 `1.0/1.0` 与增强 `1.5/1.1` INI 保持字节一致）：
   - `/mnt/c/DLSS5-5090-dll/发布打包/OptiScaler-REFramework-DLSS5-RTX30-0.4.0.zip`
   - `/mnt/c/DLSS5-5090-dll/发布打包/OptiScaler-DLSS5-RTX30-0.4.0.zip`
   - `/mnt/c/DLSS5-5090-dll/发布打包/Magpie-DLSS5-RTX30-0.4.0.zip`
   以及对应的逐包 `.sha256` 与顶层 `SHA256SUMS.txt`。

### 步骤 3：Windows 原生 Smoke 实测与包完整性核验
1. 对三个 `v0.4.0` 包执行 Windows NGX Feature 18 创建/评估 smoke，并对两个 OptiScaler 包执行完整 `FFX -> NGX -> NR` 端到端组合链路 smoke（共 5 项测试），验证全部 `returncode == 0`、`nonfinite == 0`；
2. 核验三个 ZIP 的 CRC 完整性、包内逐文件 SHA256、Windows `Get-FileHash` 与驱动数字签名状态，将完整验证结果写入 `Development/ptx-patcher/release-rtx30/v040/validation.json` 与 `packages.json`，然后清理临时 staging 目录与测试帧产物。

### 步骤 4：公开文档与版本说明全量同步
1. 新增 [`Development/doc/使用说明0.4.0.md`](doc/使用说明0.4.0.md) 与发布回执 [`Development/ptx-patcher/release-rtx30/v040/README.md`](ptx-patcher/release-rtx30/v040/README.md)，详细说明 `v0.4.0`（`PTX V4.0`）相对于 `v0.3.0`（`PTX V3.1_pack5`）的三项底层改进：
   - ① `FB04/05/06` 500 处正零转换编译期常量折叠（`mov.b16 dst, 0`，`PTX V3.8`）；
   - ② 全路径 CFG 无覆写证明解锁跨基本块 32 位源寄存器直解 `UP-Pair`（在 34 个活跃入口直解 1,288 处独立 `UP` 并删除 644 个 `mov.b32 {%lo, %hi}, %src32` 半字拆分）；
   - ③ `FB02/03/05/06` 启用省去前端冗余 `min.f16x2 448` 的 4-SASS `Pack4`（`abs` 直接折叠进 `HMUL2 |R|, 2^-8`）；
   - 汇总 38 活跃核非 NOP SASS 从 `152,076 → 145,461`（`-6,615` 条）、`PRMT` 从 `19,861 → 18,781`（`-1,080` 条）、`STL/LDL` 从 `107/108 → 99/100`、配对均值 **720p `5.61~5.66 ms` / 900p `8.27~8.30 ms` / 1080p `10.99~11.00 ms`** 及新三包 SHA256。
2. 同步更新 `README.zh-CN.md`、`README.md`（顶部版本表新增 `v0.4.0` 行，下载链接暂标“本地已生成 / 待上传网盘”，保留 `v0.3.0`、`v0.2.0`、`v0.1.0` 完整下载链接）、`CHANGELOG.zh-CN.md`、`CHANGELOG.md`、`Development/doc/使用说明.md`、`Development/ptx-patcher/README.md`、`Development/DevHistory.md`（顶部当前正式版本更新为 `v0.4.0`）与 `Development/WorkingPlan.md`。
3. 按第 0 节要求拆分为 **3 个干净的小颗粒度 Git Commit（严禁加 `Co-Authored-By`，不 push）**。

## v0.4.0执行回执（2026-11-01）

- [x] 源V4.0 SHA与大小校验；备份现场元数据和旧NR到`C:/DLSS5-5090-dll/backups/20261101-v040/`。
- [x] 五处核心覆盖并SHA核验，Magpie目录0.4.0；原宿主/转发桥/INI保持字节一致。
- [x] 三个0.4.0 ZIP、逐包sidecar和顶层SHA清单完成；0.3.0三包/清单归档archive/v0.3.0，旧0.1/0.2归档保留。
- [x] 3项原生Feature18+2项FFX→NGX→NR组合测试通过，returncode/nonfinite全0；13项Windows哈希、驱动Valid/NR NotSigned状态、CRC与全成员SHA核验通过。
- [x] staging、测试工具、帧及宿主临时日志清理，回滚备份保留；使用说明与中英文README/CHANGELOG同步。
- [x] 按代码/凭据、使用说明/回执、公开文档/状态三个干净小提交；无Co-Authored-By，不push。
- [x] 网盘上传：已上传至 [夸克网盘](https://pan.quark.cn/s/2558dd1bf036) 与 [Gofile 镜像](https://gofile.io/d/UZ4sXPCp)，旧版完整链接保留。

[完整回执](ptx-patcher/release-rtx30/v040/README.md)、[验证JSON](ptx-patcher/release-rtx30/v040/validation.json)、[三包SHA](ptx-patcher/release-rtx30/v040/packages.json)、[使用说明](doc/使用说明0.4.0.md)。本轮未重测游戏UI、FPS与运动画质。

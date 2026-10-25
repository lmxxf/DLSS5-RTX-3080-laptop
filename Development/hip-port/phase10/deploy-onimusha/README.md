# Onimusha Phase 10 独立CUDA Runtime部署回执

游戏目录：`C:\XboxGames\Onimusha- Way of the Sword\Content\`。初始部署时尚未启动游戏；本次实机发现的宿主厂商锁与镜像残留已热修，完整经过见本文后半部分。

- Linux 3 warmup/5 iter快验：896×512 median7.999ms、1280×768 median14.092ms；均Small31、Style1、Graph off、invalid0、first/last bitdiff0，32种活跃核，无对齐错误。这不是此前50/80性能表的新替代值。
- C256默认门控现为所有TierGeometry/free_geometry融合，只有`DLSS5_LAB_C256_SPLIT=1`显式退回分散路径。
- `build-runtime.sh`交叉编译当前Host和Ampere预洗牌CPU权重打包。Runtime模块探测增加sm_86；flags loader接受CUDA架构、AMPERE_WEIGHTS和C256_SPLIT配置，避免路径识别漏掉优化核。
- `LmxxfNrRuntime.dll`：5,048,942 B，SHA256 `ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353`。
- 从指定0.44底包提取DLSS5-AMD、D3D12_Optiscaler、shaders共667个文件，内容解压后逐个SHA核对；含93个Small权重、207个cso。
- `HIP/sm_86`中40个Phase10 selected hsaco逐个与冻结manifest相符，AMPERE_WEIGHTS_V2标记一致；HIP根/子目录SHA256SUMS更新。gfx1200/gfx1201已移除，HIP根无其它hsaco。
- 原INI、PTX wrapper与模型DLL已备份并核对SHA，游戏根两个旧NR DLL移除；初始部署时dxgi.dll、dinput8.dll未改；后续dxgi两字节热修见下文，dinput8仍未改。
- INI：Enabled=true、NrBackend=lmxxf、WhitePointSource=1、Preset=2、Style=1、Dx12Upscaler=dlss。
- default-config：MULTI_PASS=0.5、FAST_NUMERIC=1、AMPERE_WEIGHTS=1、CUDA_ARCH_NAME=sm_86、C256_SPLIT=0、NETWORK_FREE_RES=1、STYLE=1、HIP_GRAPH=0。

特别修正：底包FREE_RES原为0，854×480会先套720档并跑1344×768。改为1后，Windows真实D3D12/CUDA探针的PrepareFrame成功，报告`net=854x480 color_job=854x480 proc=896x512 modules_ok=40 hip=1`；wave-owned、C512、ViT gates为1，architecture=sm_86。API/Create/PrepareSession/PrepareFrame/Cancel全status0。日志：windows-probe-free.log。

备份：`C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0\`。恢复其中OptiScaler.ini、nvngx.dll_dlssnr.dll、nvngx_dlssnr.dll到Content即可恢复原PTX选择；旧INI会切回nvidia backend。部署完整哈希/原文件回执为该目录下phase10-deployment.json及backup-manifest.json。

当前游戏配置载入的模型是31块Small。底包其余公共资产按用户指定完整解压，未将本次游戏配置改动同步到其它游戏或发布ZIP。

## 2026-10-25：鬼武者首次实机误跑PTX——AmdBridge厂商锁与_storage_残留双重排查

### 首次场景与结论修正

Zero第一次进入《鬼武者：剑之道》，2K高画质、超分“高性能”，实际为 **854×480 → 2560×1440**，反馈约31帧。该次实际运行的是此前的 **ptx-patcher v0.1.0**，不能记作hip-port Phase10独立CUDA引擎的游戏帧率，也不是4K输出测试。

上一轮部署已验证Runtime自身的Windows D3D12/CUDA API、模块和输入几何，但探针直接调用Runtime，绕过了OptiScaler宿主AmdBridge的入口。部署仅清理Content根目录，也遗漏了递归子目录里的NR副本。这两处属于上一轮验收覆盖不足，本次把“双位置宿主补丁＋整树递归残留＋真实游戏Backend/Enqueue证据”补进验收。

### 乌龙1：NrBackend=lmxxf仍被物理AMD厂商检查拦截

首次日志第515行由Zero提供：`DlssNr::AmdBridge::IsAmd AMD pre-SR physical adapter vendor: 10DE, AMD: false`。该次原始日志已被后续运行覆盖，本次没有把旧行号写成当前日志的独立复读证据；原始二进制反汇编和包内源码与这条诊断一致。

包内`AmdBridge.cpp`153～171行，`IsAmd`通过PhysicalAdapterScope绕过厂商伪装，按D3D12设备LUID取真实DXGI_ADAPTER_DESC1，再检查`desc.VendorId == 0x1002`。`Before`在选择lmxxf后仍调用此函数，`if(!amd) return false`发生在`new LmxxfBackend`之前，所以仅写INI `NrBackend=lmxxf`并不足以进入自编译Runtime。

按PE静态映像基址0x180000000反汇编（不是ASLR后的绝对运行地址）：

| 位置 | 文件偏移 | 原指令/字节 | 效果 |
|---|---|---|---|
| VA 0x18002c13f | 0x2b53f | `cmpl $0x1002,0x410(%rbp)` | 比较实际VendorId |
| VA 0x18002c149，RVA 0x2c149 | **0x2b549** | **`75 03`，jne** | NVIDIA跳过下面的置true |
| VA 0x18002c14b | 0x2b54b | `41 b4 01`，mov $1,%r12b | 设置入口允许标志 |

Zero已先备份原版dxgi.dll，再把Content/dxgi.dll及Content/_storage_/dxgi.dll的0x2b549处`75 03`改为 **`90 90`（nop;nop）**。本次逐字节核查：两份均26,213,888B，与原版相比**恰好只有0x2b549、0x2b54a两字节不同**。CMP及真实VendorId未改，后续日志“10DE, AMD:true”表示这一布尔入口已放行，不是RTX变成了AMD。

- 原始备份SHA256：`aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2`。
- 两份patched SHA256均为：`f3fe9bfbfd3b4add7460713521d4e16d6d95c6fa3bf90db27e7338b6d255f35d`。
- 原始备份：`C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0\dxgi.dll`；原始哈希也与0.44底包的dxgi.dll一致。
- 此文件偏移只对应上述精确原版哈希，核查脚本强制验证原版身份、原字节及完整两字节差异。

### 乌龙2：GDK镜像子目录把旧NGX路线重新带回来

AmdBridge返回false后，宿主回退NVIDIA NGX路径；`Util::FindFilePath`会递归找文件，不止Content根。Zero在XboxGames/GDK的`Content/_storage_/`镜像子目录发现仍有`nvngx.dll_dlssnr.dll`及`nvngx_dlssnr.dll`，报告其SHA与原PTX备份一致。原部署根目录虽已移除，这两个深层副本仍足以让旧路线加载。

备份的身份已在本次重新读取核对：

| PTX文件 | SHA256 |
|---|---|
| nvngx.dll_dlssnr.dll | `4f088f382171b3b3af4e2b34cb71b162788c947a55eeefc6e81e36206c59a0c9` |
| nvngx_dlssnr.dll | `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a` |

Zero已删除_storage_两副本；本次对Content整树复查，上述两个文件名的残留数均为0。被删文件的原字节现已无法重新读取，因此“删除前副本与备份同SHA”明确归于Zero提供的热修证据；“备份SHA”和“现已递归不存在”则是本次独立核查结果，没有混写。

### 其余AMD假设的快速审计

审计底包配套源码`AmdBridge.cpp`499行、`LmxxfBackend.cpp`716行及dlssnr目录相关VendorId/0x1002引用，并核对当前自编译Runtime/bridge源码：

1. AmdBridge这条主动调用路径中，唯一直接`VendorId==0x1002`检查位于IsAmd。其余门槛为文件存在、D3D12设备/队列、后端wired、输入子矩形原点、尺寸稳定/预热及资源状态，不是另一个AMD厂商锁。
2. `HasFiles`在lmxxf分支找LmxxfNrRuntime.dll；`LmxxfBackend::EnsureRuntime`显式LoadLibrary该DLL、GetApi、Create、PrepareSession，没有发现AMD VendorId判断。`RuntimeName`仍查AMD pass1的菜单元数据，`HipRuntimeLoad`仍含amdhip64加载路径，但它们属于原Daniel/AMD路线或名称显示，没有成为当前Lmxxf链路的附加准入锁。
3. 自编译Runtime经nvcuda.dll实现兼容API。桥接优先LUID匹配，名称回退已接受0x10DE/0x1002，架构白名单含sm_86。前次已修复sm_86模块目录枚举和配置加载，删除AMD目录后会选择HIP/sm_86。
4. `gfx1201_target`仍是ABI遗留字段名/值；已查宿主LmxxfBackend不使用它作厂商拒绝。SubmitPulse仍有AMD驱动指纹范围，它影响可选提交优化，NVIDIA退回普通提交；Small的pdl=1/0及swin_run=1/0不是再次拒绝整个CUDA网络。当前没有发现另一个阻断调用的AMD专属条件。

以上是针对本版本当前路径的快速静态审计加实际调用证据，不宣称全部可选功能、所有GPU/资源格式都已验收。

### 热修后的真实游戏调用证据（与首次场景分开）

本次读取的OptiScaler.log是 **15:17:21启动、15:19:58正常shutdown** 的后续运行，源日志SHA记录在hotfix-audit.json。该轮DLSSContext日志为 **1280×720 → 2560×1440**，不是最初854×480场景，不能混在同一FPS/分辨率结论里。

- 第512行及后续：physical adapter vendor **10DE, AMD:true**。
- 第513～526行：构造LmxxfBackend、assets/modules路径、Create成功并session ready。
- 第527行：PrepareFrame报告 **`modules_ok=40 hip=1`**，`wave_owned=1/1 c512_m32=1/1 vit_proj_n64=1/1 vit_stream=3/3 multi_pass=0.5`。
- 第529、531～534行：eval1～5，enqueueCalls0→4、betweenHits0→4、producerSubmitted/continuationSubmitted0→4，**lastEnqueueRc=0、submitFailures=0**。
- 15:19:58：LmxxfBackend正常shutdown。启动时单次“upscaler could not restore state this frame”之后已经进入正常Record/Enqueue，没有把这一条启动跳帧当作持续失败。

这证明后续实机确实走到了独立CUDA链路。日志没有给出新的、与首次同设置的FPS验收，因此本次不补造“修复后帧率”。`lmxxf diagnostic: mode=off`仅指诊断旁路关闭，不是神经网络关闭。`LMXXF_WEIGHTS_DIR unset`警告随后已有weights=1和PrepareFrame成功，也不是本轮权重加载失败。

根目录与_storage_的LmxxfNrRuntime.dll已分别核对，均为`ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353`。未修改Runtime或40个Phase10核。

### 清单与回滚记录

备份目录下`backup-manifest.json`新增原版dxgi条目、patched SHA/字节和两个部署位置；`phase10-deployment.json`及仓库deployment.json同步记录补丁、原版备份、_storage_清理、整树无残留与真实游戏证据。旧“dxgi未改”的字段已移除，dinput8仍保持原文件。

原版dxgi保留未改；回滚厂商补丁时应同时恢复两个位置，避免镜像副本继续加载另一版本。PTX三文件的原始备份仍完整。核查与记录脚本为`Development/hip-port/phase10/deploy-onimusha/audit_hotfix.py`，关键当前日志摘录为hotfix-live-evidence.txt；完整日志快照/反汇编/临时源码放在忽略的artifacts。本次没有修改其它游戏、发布ZIP，也没有将DLL或模型提交到Git。

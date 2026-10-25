# Phase15：长期正确性回归；性能优化暂停

基线固定为 **Phase14 selected + 新720p F32 gold**，起点9c27a1c/830185d，工作树干净。本轮没有生产内核/Host算法变更，没有C32性能候选，没有性能计时成绩；不push、不部署，不改游戏/Magpie、共享assets或发布包。

**状态分开记录**：布局/确定性/输入更新回归通过；代表性HDR与整体画质验收未完成；原45dB全局门槛未过，性能优化暂停。

## 输入来源与缺口

详细证据 [input-audit.md](input-audit.md) / `input-audit.json`，已单独提交 **cbbc72e**。

- 找到一张带GameDVR与sRGB元数据、已目视确认的《明末》1920×1080武器菜单PNG。原始SHA `a055f4e3e43ee2094ca76433b8c57587e35eb5a73a6013622f540a5d52d1d29a`。这是**一张真实来源SDR菜单截图**，不是原始场景线性HDR，也不是多帧游戏过程。
- 旧文档的真实HDR `D:\DLSSNR-Lab\hip-backend\live-menu-before.f16` 当前机器不可用；Temp/input.f16全零；Magpie smoke input为人工渐变（SHA `8f32c03e17faf3267434c84ff4b7c071b09796a45d965b5ae5667298ae45eafb`）。不把它们冒充实拍。
- 冻结副本在忽略的`artifacts/inputs/source-menu.png`、`source-smoke.f16`；生成器优先读取这些已验SHA副本。未写原始Windows目录，也未要求Zero重新进游戏。

单张菜单不足以代表游戏/HDR场景。按本轮“真实输入不足则暂停性能侧”要求，**没有进入新的C32优化实验**；也没有把正确性快验时长包装成50/80性能成绩。

## 56配置、7几何、整幅动态更新

每个几何8个输入配置，实质为5种不同编码图像加3个白点等价项：真实菜单sRGB直通、该菜单显示线性化后再编码、整幅翻转/移位/通道变换与增益的衍生帧、既有codec half-bit RGB fixture、既有smoke渐变。菜单变换属于**合成动态输入**，不能算第二张真实捕获。

codec fixture使用仓库`d3d12_native_codec_test.cpp`的decode/proxy RGB规则，alpha显式置1；HDR由其512倍配对派生。源代码SHA、原图SHA、编码输入SHA、源/工作域范围均在`input-manifest.json`。该fixture与衍生输入覆盖原始数值**0..512**及白点**512/1**配对；真正RE Engine原始HDR数据仍为0份。

预处理采用已有encode shader的手动白点、曝光1、soft-knee/sRGB公式，再进行FP16工作面舍入；是**CPU fixture预处理**，不声称D3D12 shader字节一致或真实游戏HDR合成通过。由SDR线性化×512得到的图也明确标为模拟HDR。配对归一化后编码字节应相同，21组白点配对的输入及三种网络模式输出均0bit；这不验证游戏曝光资源绑定。

| 名称 | 处理尺寸 | 可见尺寸 | Small ViT token |
|---|---|---|---:|
| 512 | 512×512 | 512×512 | 64 |
| 480-fit | 896×512 | **854×480** | 128 |
| 1024 | 1024×768 | 1024×768 | 192 |
| 640 | 640×640 | 640×640 | 144 |
| 1152 | 1152×640 | 1152×640 | 240 |
| 720 | 1280×768 | 1280×720 | 240 |
| 1024-square | 1024×1024 | 1024×1024 | 256 |

图像按visible尺寸做明确的双线性变换，右/下不足部分采用不重复边缘的镜像填充。854×480→896×512只验证离线working-surface/network几何，不冒充D3D12游戏接入验收。

同一Network、同一CUDA输入/输出地址，逐次**整幅上传**，输出先填NaN哨兵；8输入连续两遍并恢复A。每种图都重复核验，源图A/B改变像素比例约99.998%，输出确实随内容改变。没有只改一个像素，也没有把上次处理结果当下一次原图。

两轮完整入口重放：每轮27进程组、375次动态/校准Enqueue，加27次资源重放；共 **750次帧调用 +54次资源重放**。两轮所有输入/输出SHA相同，全部重复输入first/last0bit、invalid0。56配置correct256/400完整处理面逐位相同。所有默认及correct256的32种活跃核LOCAL均0；资源追踪不调用ElapsedTime、不报告性能。见`regression-runs.json`、`replay-runs.json`、`replay-verification.json`。

## 每输入精度口径与新质量边界

[image-results.md](image-results.md)逐项列出全部56配置；`pinned-image-outputs.json`冻结输入/Native/F32输出SHA，重测会严格比对，不能静默接受变动。

PSNR固定 **peak=1，在可见区域的编码工作RGB输出域**，不是以每张图最大值作peak，也不是原始线性HDR的peak512。maxabs同域。两种精度接收完全相同工作输入，F32是Phase14配对、同一Small31/Style1/FP8-F16权重的F32累加链。先重现900/1080旧gold与新720gold0bit，才用于新图像。此分数只衡量Native相对F32参考的精度，不等于模型相对原图的画质，更不是实机观感验收。

同一真实SDR菜单源在各几何的结果（不是7张独立实拍）：

| 处理/可见 | PSNR peak1 dB | maxabs |
|---|---:|---:|
| 512×512 | 57.033622 | 0.042611837 |
| 896×512 /854×480 | 59.558024 | 0.030074537 |
| 1024×768 | 60.170567 | 0.045806646 |
| 640×640 | 59.417262 | 0.035768986 |
| 1152×640 | 59.800880 | 0.030112743 |
| 1280×768 /1280×720 | 60.247254 | 0.043955266 |
| 1024×1024 | 60.881225 | 0.036385596 |

**新增未达门槛样本**：1024×1024的codec-ramp，PSNR **43.436806dB**、maxabs **0.054382861**。white1/512是同一编码输入的两个尺度配置，不能算两张独立失败图。两轮结果一致、256/400一致且无NaN/状态故障；差异的具体层级来源尚未定位，不猜测根因、不改精度掩盖。

**43.577948dB和43.436806dB都低于45dB。原45dB全局门槛没有通过。** 单张菜单的高分不代表全部画质结论。代表性真实HDR缺口与这项质量限制同时保留，性能侧继续暂停。

## 三档规范基线与长期原语入口

| 档位 | 对可信F32 PSNR | maxabs | Native对基线 | invalid/first-last/LOCAL |
|---|---:|---:|---|---|
| 720p1280×768（可见720） | 43.577947912339 | 0.050935506821 | Phase14新正确输出0bit | 0 /0 /32种全0 |
| 900p1600×1024（可见900） | 46.975322410562 | 0.040045499802 | Phase14与Phase12均0bit | 0 /0 /32种全0 |
| 1080p1920×1152（可见1080） | 46.100947087035 | 0.041602730751 | Phase14与Phase12均0bit | 0 /0 /32种全0 |

新720 F32 gold仍是SHA `149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5`，没有替换900/1080既有gold。

同时复跑256坐标、172项16..256合法token/实际QKV/NaNInf入口覆盖，以及CPU按明确`rcp.approx`口径对八块 **1966080 AV字节0bit**。这里“实际QKV”来自实际CUDA执行的**全零Prepare预热**（Phase15B已核实输入归属），不是游戏捕获；原始样本与来源在`regression-provenance.json`。原始保留FP8字节的兼容测试没有扩称IEEE NaN语义。

最终从默认源码全量重编40/40并实际CUDA load/resolve **1918entry**，全部模块SHA与Phase14相同。`selected-modules.sha256.json`、`reference-modules.sha256.json`、`cuda-load-verification.json`、`host-provenance.json`、`platform-provenance.json`、`validation.json`记录参考链和质量门；18项既有Python/LLVM回归通过。未改变Graph off/Small31/Style1默认，也未设置GPU锁频或功耗。

## 一键重测

依赖本机只读权重、Phase14 Native/gold与Phase1冻结F32档案；不写这些档案：

```bash
python3 Development/hip-port/phase15/run_all.py --tag my-retest
```

入口已实际跑过`replay`整轮：编译/实际加载40模块、原语、金标准校准、56输入动态/几何回归与SHA比对。使用新tag，拒绝覆盖旧输出。原图/渐变优先读取已验SHA的phase15冻结副本；派生输入可按生成器完整重建。输出不同即失败，不自动换gold或放宽45门槛。

单独分析已有记录：

```bash
python3 Development/hip-port/phase15/analyze_suite.py --tag regression
python3 Development/hip-port/phase15/validate_all.py --tag regression
```

清理仅本轮重复模块、LLVM、可再生编码输入；保留最终40模块/PTX/生成源、真实源PNG/fixture副本、新gold引用、QKV/AV样本、输出SHA与原始日志。重复的不可覆盖输出按SHA硬链接去重；详情cleanup.json。没有新的性能数据，正确性快验时长不会替代50warmup/80iter性能测量。

## 下一步停留在质量侧

先补回**已有**原始HDR捕获或多帧素材（旧D盘档案），并逐层检查1024² codec-ramp差异来源，再决定是否恢复C32性能工作。本轮不要求Zero重新进游戏，不强行安排Phase16。继续保留Phase14实现，无新性能保留项或性能负收益结论。


## Phase15B 质量诊断追加

见 [DIAGNOSTIC15B.md](DIAGNOSTIC15B.md)。本轮新增严格的Prepare后启用与消费输入SHA门控；历史QKV fixture已证实属于零预热，数值数据与gold保持不变。新诊断核验实际冻结输入，未修改生产默认或45dB门槛。

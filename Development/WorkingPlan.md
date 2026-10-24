# v0.1.0 工作计划：PTX 主线与发布结构

当前产品是 `Development/ptx-patcher/`，以原版 **310.9.16.0 `nvngx_dlssnr.dll`** 为输入，目标为 RTX 3080 Laptop / Ampere `sm_86` 的 **31 块 Small 模型**。工程首版为 **0.1.0**；上游 AMD 包的 **0.44** 仅表示输入来源。

## 目录约定

`Development/` 严格只放：

- `DevHistory.md`：按时间记录工程工作、实验、反证与部署回执。
- `WorkingPlan.md`：当前架构、入口和后续工作。
- `ptx-patcher/`：当前产品代码、发布工具及所有相关工作材料。
- `hip-port/`：平行保留的附加/实验路线。

`ptx-patcher/` 内：

| 路径 | 职责 |
|---|---|
| `build_sm86_dlls.py` | 哈希门控的原始 DLL 输入、15 个 Fatbin 编译与 PE 组装 |
| `dlssnr_patcher.py` | PTX/PE 解析、转换及宿主架构适配 |
| `ptx_mapped.py` | 完整目的操作数定义统计、多定义过滤和严格块内诊断模式 |
| `pe_fatbins.py` | O4 超槽位时的 PE 扩容后备；当前发行 DLL 全部原槽位 |
| `bench_nvngx.dll.cpp` | D3D12 timestamp、合成场景/天空、输出检查 |
| `sky-audit/` | 天空色带排查、控制实验、有限值转换检查和历史失败 |
| `magpie-native/` | 原生 Feature 18、Preset 2 EXE 补丁、验证与正式部署 |
| `magpie-fix/` | 旧 add-on 入口、缺 SR 库与窗口测试的历史修复材料 |
| `release-rtx30/` | 三个发行包的组装、版本、部署脚本与发布回执 |

## 当前 PTX 架构

1. 只接受 SHA256 `2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f` 的原版 DLL。
2. 用位重排与 FP16x2 乘 256 完成 E4M3 解包；以 FP16 加 2 的 RNE 网格处理 E4M3 次正规量化，普通值走紧凑位打包。
3. 将 FP8 `m16n8k32` 映射到两次 FP16 `m16n8k16`，保持原生 Warp fragment 坐标。
4. 拒绝 packed 目标、FP8 中间寄存器或 FP16 来源在 entry 中多定义的 mapped，包含花括号向量加载和内联指令。默认保留单定义跨块转发，不额外量化；严格模式和量化模式供诊断。
5. 全部 Fatbin 以 O4 编译、验证加载后组装输出；当前发布 15/15 原槽位。保留 PE 扩节后备能力，不降 O1 偷换发布判据。

转换辅助函数的有限值 `0 bit-diff`，与整个默认转发网络的数值等价是两个命题。上游 shared-bug 输出一致也不是正确性证明。

## 三包当前状态

| 包 | 当前默认 |
|---|---|
| OptiScaler-REFramework | NR → DLSS SR，Preset 2 / Style 1 / 单遍，保留 dinput8 与完整辅助库 |
| OptiScaler 常规 | DLSS/FFX → NR → DLSS SR，完整 FFX loader/provider，默认细节 1.5、色彩 1.1 |
| Magpie | 原生 DLSSNR Preset 2 / Style 1 → DLSS_SR，无 ReShade/add-on/外置权重 |

Magpie 0.6.6 原后端把 Preset 写死为 0。`magpie-native/patch_preset2.py` 对已知原始 EXE 做最小字节守卫补丁，输出 SHA 固定为 `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea`。JSON 只配置 Style 等原生参数，不伪装它能改变硬编码 Preset。

源码仓不放 DLL、ZIP、模型权重、GPU 模块或临时图像。当前发行包位于本机 `C:\DLSS5-5090-dll\发布打包`；大二进制与恢复备份独立于 Git。

## 已验证

- 转换有限域：GPU 双通道各 63,488 个有限 FP16 编码零差异。
- Fragment 坐标：A/B 768 个标量槽位检查零错位。
- mapped 控制：天空逐行红绿变号 106→0；仅多定义过滤且不额外量化恢复 O4 容量和速度。
- 发布：原槽位 15/15 O4；NR DLL SHA256 `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`。
- 《鬼武者》与《剑星》用户实机验收；当前日志有约 17.5 ms / 18.4～18.9 ms NR 总耗时示例，不据此补写整机 FPS。
- Magpie 原生：实际 720p 动画窗口到 4K，960 次成功、0 失败；NR GPU 约 15.9 ms，完整窗口评估约 36 FPS。
- 历史上游 O1 最低 GPU 时间比较为 2.08～2.25× 提速；当时双方的错误 mapped 一致，不再引用为正确性证据。

## 回归入口

```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

移动脚本或修改打包路径后检查 Python 语法、文档链接与引用路径。更改模型转换时，再跑有限值 GPU 检查和同输入输出对照；更改发布链时，检查原生模型真实分发、逐文件 SHA256 与 ZIP CRC，而非只看 DLL 注册成功。

## 后续工作

1. 收集 Magpie 原生路线在《光环》同一场景的整机 FPS，与旧路线做同负载对照；不把 `1/NR耗时` 当整机帧率。
2. 若要提升完整链路 FPS，分别测 NR、SR、共享纹理/fence、捕获与呈现，避免只改模型外的重复处理。
3. 扩展更多 RTX 30 设备与游戏验收，记录显存、功耗、质量档位和输入格式。
4. 如需更新 NVIDIA DLL/Magpie 版本，先重新核验输入哈希与指令布局，拒绝复用旧偏移。
5. `hip-port/` 继续作为研究材料，独立优化与结果不写成默认 PTX 发布成果。

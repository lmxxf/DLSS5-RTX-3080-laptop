# ViT流式注意力与可选跨帧复用

2026-09-20从AttExp选入main的只有：精确流式attention、自适应ViT复用R3、相同输入延长缓存与融合anchor提交。INT4、2:4剪枝、K/V合并及C32稀疏均未选入。

正常HIP构建直接使用hip/deep_fast.hip和hip_reference_network.h，无需实验生成器。精确流式attention始终使用，保留原数学/舍入顺序。自适应默认关闭，完整计算不增加近似；开启后是有损预测，不保证所有场景画质等价。

在native-game-flags.txt中启用：

```
DLSS5_VIT_ADAPTIVE=1
DLSS5_VIT_REUSE_PERIOD=4
DLSS5_VIT_REUSE_HOTKEY=1
DLSS5_HIP_GRAPH=0
DLSS5_HIP_VIT_BYTE_STREAM=0
```

要求默认fast/pooled HIP管线、31–38未跳层。F8切换自适应/完整计算；F6仍是整个效果开关。若FPS信息显示已开启，会附加AE/EXACT，不强行开启用户关闭的信息层。DLSS5_VIT_ADAPTIVE=0或不设置始终完整计算。模式2/3留作验证（强制完整/固定GPU周期），不推荐用户配置。

特征阈值默认global0.22/local1.0，原图相邻2×2个32像素块阈值0.35；都是启发式判据。实际重算才更新anchor，近似帧不递归更新；模式切换、输入/seed/history变化、几何变化及超过500ms间隔重置。全量ViT输入位相同（含padding/signed-zero）可超过period延长缓存，过期后输入一变立即重算。原图anchor提交已融合到finish。

gain默认从当前资产block31–38的contract/projection尾部1024通道缩放以double连乘后转float计算；无需额外下载gain文件。DLSS5_VIT_REUSE_GAIN仍可指定4096字节f32文件用于对照。诊断日志DLSS5_VIT_ADAPTIVE_LOG会同步读回，不能用于正式性能测试。

**DLL与HIP模块必须成套更新。** ViT入口增加了可空门控参数，旧DLL不能混用新模块。标准hip/build-modules.ps1仍默认编译gfx1200和gfx1201；实际游戏模块位于DLSS5-AMD/native-game-tiled-assets/HIP。此次只迁移源码，不覆盖运行中的游戏或发布包。

验证工具：benchmark_vit_reuse.cpp含受控输入回放；test-main-vit-reuse.ps1比较main与已验R3的逐帧输出（900/1080、静止/平移/小遮挡、完整/自适应、历史开启）；vit_reuse_gate_check.cpp覆盖相等输入、padding、signed-zero、年龄、NaN及融合提交。GPU测试脚本使用现有amd9070实验室路径并检查游戏/Magpie退出。

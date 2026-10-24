# 小窗口输入与 Magpie 后接 FSR4

候选开关：`DLSS5_FIT_INPUT=1`。未开启时仍只接管 1920×1080。

输入宽、高分别在 1～1920、1～1080 范围内时，codec 把图像双线性缩放到居中、保持比例的整数视口，补黑边到 1920×1080；网络仍使用原 1920×1152 处理网格。decode 按同一视口逆映射，将结果合成回原始尺寸。运动采样的坐标、位移按相同视口换算，补边运动为零。1 像素运动图不启用时序。原 1080p 走原 shader 分支。

Magpie 效果组：

1. `FSR3\FSR3_SR`：`scalingType=0`（相对输入）、`scale=1,1`。
2. `FSR4\FSR4_SR`：`scalingType=1`（适屏）、`scale=1,1`。
3. 保留 XeSS FG。

选择第一个 FFX context（包括超限提示），直到该 context 销毁；后面的 FSR4 不接管，即使输出也不超过 1080p。`ffxDestroyContext` 的 allocationCallbacks 必须原样转发；钩子所在的 loader 在进程内固定，避免停止缩放卸载模块后 trampoline 指向失效地址。Magpie 每站独立提交 D3D12 工作，然后 Signal→D3D11 Wait→CopyResource，因此在第一站 ExecuteCommandLists 返回前补交网络工作即可交给下一站。该宿主在 dispatch 后把输出从 UAV 转回 COMMON，钩子跟踪同列表、同资源的后续 barrier，按提交时状态处理。

开发部署：

- 本地候选：`release/fit-input/`，远端：`D:\DLSSNR-Lab\fit-input\`。
- 退出 Magpie 全部进程后，`deploy-fit-input.ps1 -Action Deploy`；脚本验候选 SHA256，备份旧 DLL/3个shader/flags/config，再改本机安装和效果组。
- 回退：同一脚本 `-Action Restore`；备份在远端 `before-fit-input\`。
- 不修改游戏目录、不打发布 tag、不更新发布 zip。

验证：

- `Development/tests/input_geometry_test.cpp`：穷举全部 2,073,600 合法尺寸，验证视口/补边/正逆坐标和 256 字节 row pitch。
- `Development/tests/compile_fit_shaders.cpp`：生产 D3DCompiler 编译36个 codec/temporal shader 组合。
- `Development/tests/fit_codec_gpu.cpp`：9070 XT 上真实 codec encode→独立 neural 资源→decode→CopyTextureRegion→回读，1914×1063、1280×720、1440×1080、641×479、1920×1080 全部通过。强度0,0时原图逐字节还原；补边为黑，行距哨兵完整。该测试不代表网络画质或性能验收。
- 整条 Magpie 流水线的现场结果见 DevHistory 后续记录。

# RTX 3080 Laptop PTX 修补

当前默认：拒绝pack目标、两路FP8中间寄存器或FP16来源在entry内存在多定义的mapped（包含向量加载定义），允许单定义跨基本块转发；合法mapped保留原fast的shfl/shfl/selp，不额外量化。

原版310.9.16.0有SHA256门控。需要WSL NVIDIA CUDA Driver、Python numpy、libzstd；不依赖/tmp源码。

```bash
python3 Development/ptx-patcher/build_sm86_dlls.py --input /mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll --output /mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll --workers 3
```

2026-10-24控制变量实测：默认版15/15 O4，全部原槽位容纳，PE保持7节；720p天空红绿变号0次，高频RMS=.000102701；GPU median 720p/900p/1080p为15.829/24.474/32.036ms。已部署游戏。转发沿用原fast精度语义，不宣称与完整E4M3转换逐位等价。

诊断选项：`--mapped-mode strict`要求源定义、转换、pack与MMA同基本块；`--quantize-mapped`为转发源显式加E4M3量化。两项均增加过本机实测耗时。源码保留新增PE节装载超槽位O4的能力，但当前默认产物没有使用它。

回归：

```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

控制实验和部署回执见[天空排查](sky-audit/去量化控制变量回执.md)。三个发行包、实机数据与安装说明见[仓库主文档](../../README.zh-CN.md)。

生产代码及发布、天空排查、Magpie原生适配材料都在本目录；`../hip-port/`仅为附加实验路线。

### 2026-10-26：V2 偶奇 K16 零洗牌默认

`build_sm86_dlls.py` 现默认使用同lane偶/奇K拆解，仍为multidef_nq、15/15 O4。默认输出新名字 `nvngx_dlssnr_sm86_v2.dll`，保留旧fast；`--mma-layout legacy`可构建旧拆解对照。浮点累加顺序改变，不宣称旧输出逐位相同。三档正反实测约10.2/15.3/20.3ms，比旧版约1.56～1.61×；[完整回执与V7分析](v2/README.md)。

### 2026-10-26：当前推荐 V2.1（maxnreg 控制胜出）

新推荐为 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v21.dll`：只将FB00/03/04/05/06的现有maxnreg升至255，保留V2图和权重；三档对V2严格0bit，同轮median约6.66/9.70/12.78ms。使用 `python3 Development/ptx-patcher/v21/build_recommended.py` 可按固定SHA全量重建。[完整回执](v21/README.md)。通用构建器无cap参数仍为V2基线；旧V2与正式发布包保留。

### 2026-10-26：v0.2.0 已正式部署与本机打包

主fast、鬼武者（含_storage_原版dxgi恢复）、剑星、Magpie已统一V2.1；常规包与剑星默认1.0/1.0，附OptiScaler-增强风格.ini。三个0.2.0 ZIP及SHA已生成，旧包归档，Windows smoke通过。[正式回执](release-rtx30/v020/README.md)。

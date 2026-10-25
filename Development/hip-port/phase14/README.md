# Phase14：修复小token attention，建立可信720p新基线

唯一性能/旧输出基线 **Phase12 selected**。起点41042b6，工作树干净。本轮允许720p正确性输出变化；900/1080仍对Phase12严格0bit。未改ptx-patcher、共享assets、游戏/Magpie或发布ZIP，不push。

**保留**：legacy attention两处预洗牌ABI修复；Host对<=256token默认选用已验证等价、略快的400 transposed-score路径。修复256导出仍保留，benchmark可以显式选择。**未保留**：任何精度下降、LDS索引猜测、单分辨率特判、FFN即时contract、Graph或跨h2预解包。

## 已证明的根因与修复

详见 [correctness.md](correctness.md)。构建器给Q和xb插入了Ampere预洗牌，但legacy函数的QK/PV消费者漏改，通用WMMA又做一次RDNA4→Ampere转换。`phase14_transform.py`严格限定该函数，将两个A侧消费者改用`sm86_wmma_fp8_preshuffled_a`，B侧及C/D/数值运算保持。坐标单点证明Q重复洗牌破坏score、P重复洗牌只破坏PV；LDS转置、概率行分母与PV原索引均正确。n=16即可复现，不是n%64尾块错。

256坐标×独立错误/修复组合，全部修复后原始u32差异0。172项两种累加覆盖16..256步长16的全部合法token数、32head、非均匀/末token/边界/subnormal/±0及实际QKV，修复256对400及原始布局规范参考均0字节差异。浮点NaN/Inf经真实clamp/pack入口后也一致；保留byte7f/ff的兼容检查不扩称IEEE NaN支持，详见正确性报告的域说明。

整网额外检查512×512（64token）、896×512（128）、1024×768（192），correct256/400输出0bit、invalid0、首末帧同、32/32 LOCAL0。720是240token，已正式双轮验收。没有只修1280×768一个条件。

## 新720p F32金标准

先重建未修复F32 control，目标模块SHA与归档精确一致；control/修复链均复现900/1080已有gold0bit，再生成新720 reference。冻结F32的39模块不变，仅修复目标模块ABI，Host/权重打包配对校准；这里F32指同一FP8/F16权重的F32累加参考，源码近似倒数口径保持。

新文件：`artifacts/gold/f32-720p-1280x768.rgb32`，SHA256：

`149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5`

真实首块245760 AV字节对CPU-F32全部一致。八块共1966080字节，CPU精确除法仅一个FP8中点差异；已精确定位源码`rcp.approx`把1.0625变成1.062500119（0x38→0x39）。独立CPU矩阵/概率/分母/PV，仅单独匹配这一CUDA倒数原语后，八块AV全部0bit。没有用完整GPU attention输出当参考。最终正式Host不强制选桶又重现三档F32 gold0bit，见`gold-native-default-check.json`。

720可见1280×720相对本轮新gold：**PSNR43.57794791233917dB、maxabs0.05093550682067871、invalid0**；原Phase12完整720输出改变2947224个f32元素，为授权修复变化。不是复用Phase13的400诊断值，也不再拿旧错误比较做验收。

900/1080可见F32 PSNR **46.975322410562406 / 46.100947087035124dB**、maxabs0.04004549980163574/0.0416027307510376，不变。

## 正确256与400的速度选择

Graph off，Small31/Style1，50warmup/80iter，默认DVFS、140W上限；每行min/median/Wall/PROFILE_TOTAL及遥测独立保留。PROFILE_TOTAL是另一个插桩帧，不与median拼成“launch气泡”。先两组ABBA，再按两个顺序配对，所有接近持平/负方向样本都在 [results.md](results.md)。

最早256/400 median14.114/14.115几乎平；反向40014.121 vs25614.222。第二组ABBA也是正向几乎平、反向400微小正向。不能据此宣称大提速。独立插桩的8次attention核累计在这些控制中：256约0.301～0.317ms、400约0.260～0.270ms；这是实际计时而非Regs/静态指令推算，也不直接等同整帧收益。

后续原生Host验证的两个配对400均微小正向，最终默认改为400，并重新编译正式Host、再跑最终两轮：

| 720p路径/顺序 | GPU min / median | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|
| corrected256先跑 | 14.006 / 14.182 | 14.264 | 13.627392 |
| default400后跑 | 14.076 / **14.147** | 14.245 | 13.498368 |
| default400先跑 | 14.204 / **14.381** | 14.468 | 13.714240 |
| corrected256后跑 | 14.368 / 14.424 | 14.517 | 13.995008 |

只快约0.035/0.043ms，属于小收益，不宣称锁频因果。400与correct256整网及原语逐位相同，没有精度换速度。Host两个选桶位置（byte-stream与普通路径）同时更新，对所有<=256token生效。`DLSS5_LAB_ATTN400=0`只在`DLSS5_LAYER_BENCH`中强制correct256；运行时没有此环境开关，默认400。

## 最终原生默认验收

默认源码全量重编40/40模块并实际CUDA load/resolve **1918entry**。7个包含legacy导出的模块变化，33个SHA不变；源码与模块Hash见 `selected-modules.sha256.json`、`cuda-load-verification.json`、`final-provenance.json`。诊断probe的额外导出不在这40模块集合内。

| 档位/轮次 | GPU min / median | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|
| 720p正向 | 14.076 / 14.147 | 14.245 | 13.498368 |
| 720p反向 | 14.204 / 14.381 | 14.468 | 13.714240 |
| 900p正向 | 23.375 / 23.722 | 23.882 | 22.387712 |
| 900p反向 | 23.586 / 23.885 | 23.996 | 21.772288 |
| 1080p正向 | 31.347 / 31.826 | 31.926 | 28.646400 |
| 1080p反向 | 31.250 / 32.111 | 32.206 | 28.637216 |

900p对应Phase12对照median23.640/23.998，1080p31.681/32.100。900方向不同，1080本轮分别慢0.145/0.011ms，不隐瞒这点，也不把默认DVFS/运行顺序波动硬归因代码；未宣称这两档提速。

两轮三档：**invalid0、首末帧0bit、32/32 active LMem0**；720对新正确基线0bit，900/1080对旧Phase12 0bit。720C256wave2门控保持，无misaligned address。完整每行遥测/控制/32核表在 [final-results.md](final-results.md) / [results.md](results.md)，质量门 `quality.json`。

## 复测入口

已有本机Phase12与Phase1冻结档案/只读权重时：

```bash
python3 Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip Development/hip-port/phase14/artifacts/selected/modules
python3 Development/hip-port/phase14/build_host.py
python3 Development/hip-port/phase14/verify_modules.py
python3 Development/hip-port/phase14/prepare_reference.py --verify-existing
python3 Development/hip-port/phase14/run_benchmark.py
```

正式计时之前单独开启遥测，GPU工作顺序执行：

```bash
nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.mem,power.draw,temperature.gpu,utilization.gpu --format=csv,noheader,nounits --loop-ms=500 > Development/hip-port/phase14/telemetry-retest.csv
```

计时脚本自动新名字，拒绝覆盖旧证据；720用correct256对照，900/1080用Phase12模块，同轮与反向。`final_quality.py`接受新轮次名字。若忽略的参考fixture已清理，去掉prepare_reference的`--verify-existing`，它会先重建control/校准9001080、重建新720gold并校验固定SHA，绝不静默换金标准。

原语/CPU证据重现顺序：

```bash
python3 Development/hip-port/phase14/build_fixed.py
python3 Development/hip-port/phase14/build_probe.py
python3 Development/hip-port/phase14/trace_layout.py
python3 Development/hip-port/phase14/coverage.py
python3 Development/hip-port/phase14/actual_qkv.py
python3 Development/hip-port/phase14/build_capture_host.py
python3 Development/hip-port/phase14/capture_reference.py
python3 Development/hip-port/phase14/rounding_audit.py
python3 Development/hip-port/phase14/check_small_geometries.py
python3 -m unittest discover -s Development/hip-port/hip -p 'test_*.py'
```

18项Python/LLVM回归通过。诊断参考构建与几何快验使用0warmup/1iter，只作正确性，不混入50/80性能。清理后prototype/F32目录只保留变化模块，重跑Host前build_fixed会补齐冻结的39模块。全部大二进制在忽略artifacts，保留最终40模块/PTX/生成源、新gold、小样本、哈希、CPU证据及原始遥测；清理仅本轮重复副本/LLVM，详见cleanup.json。

## Phase15建议

把新720金标准纳入长期回归，再补真实帧/动态输入下的Style1、HDR输入范围和更多free-geometry样本，保持当前已证明正确的reference链。性能侧以新的正确输出为基线重新看C32热点，不原样重试FFN即时contract、跨h2或Graph；若转向bridge集成，另开阶段验证，不把本轮源码/本机benchmark当作已经部署到游戏。

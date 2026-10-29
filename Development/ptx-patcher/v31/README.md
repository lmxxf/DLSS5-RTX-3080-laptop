# PTX V3.1 Pack8 / Pack5 / Quad实验

结论：B pack5两轮三档全部双向净提速，作为非0bit胜出实验候选保留。 A收益不稳定；C首轮1080p回退。生产V2.9_fast及5处部署均不覆盖。

## 原语与算法

以SHA55b51876的V2.9_fast为基线。A仅将and清符号替换为abs.f16x2；B改为ties-toward-zero的简化舍入；C在B上沿用v24同基本块/无guard/唯一消费者/作用域检查，在原两条转换位置保留读取，并以PRMT7531拼接，同时启用up因子A。C是融合＋up联合候选，不能把全部收益归给融合。

每候选两通道排列×65536 half位型×256对侧poison，共33,554,432对：A相对V29为0 mismatch；B每种排列105826对不符，单通道158个位型不同；C双输入quad相对两个B pack为0 mismatch。涵盖NaN/Inf/±0，但不是穷举全部2^32输入组合。符号对称的ties-toward-zero不等于对任意数据分布无偏。

独立ptxas O4 core验证旧9/A8/B5条，abs折叠进HMNMX2绝对值修饰符。四元素小核两个B pack＋拼接为11条核心，quad为9条，PRMT从3→1。SASS原文和opcode列表均保留。

## 三档配对与复测

首轮72次（3候选×3档×正反各ABBA/BAAB），有收益的B及低分辨率获益的C补48次复测，另4次快验。每正式进程50warmup/80iter，720 sky、900/1080 scene，均值为四个进程GPU median的平均；未锁频、不剔除波动。候选分别对自己的括号基线。

|轮次|候选|宽度|V29 ms|候选 ms|下降|正/反下降|
|---|---|---:|---:|---:|---:|---:|
|first|pack5|1280|5.82800|5.71275|1.978%|2.006% / 1.950%|
|first|pack5|1600|8.52750|8.38475|1.674%|1.734% / 1.615%|
|first|pack5|1920|11.98600|11.57100|3.462%|1.539% / 5.294%|
|first|pack5_quad|1280|5.84650|5.69525|2.587%|2.592% / 2.583%|
|first|pack5_quad|1600|8.58900|8.37900|2.445%|3.426% / 1.459%|
|first|pack5_quad|1920|11.41675|11.57375|-1.375%|-0.898% / -1.847%|
|first|pack8|1280|5.81950|5.89825|-1.353%|-3.173% / 0.425%|
|first|pack8|1600|8.51875|8.44125|0.910%|1.184% / 0.640%|
|first|pack8|1920|11.19400|11.19125|0.025%|-0.098% / 0.147%|
|repeat|pack5|1280|5.87675|5.77950|1.655%|1.753% / 1.557%|
|repeat|pack5|1600|8.64600|8.46125|2.137%|1.785% / 2.482%|
|repeat|pack5|1920|11.27500|11.12300|1.348%|1.373% / 1.324%|
|repeat|pack5_quad|1280|5.89600|5.73950|2.654%|2.700% / 2.609%|
|repeat|pack5_quad|1600|8.63650|8.48150|1.795%|2.019% / 1.573%|
|repeat|pack5_quad|1920|11.29075|11.33675|-0.407%|-2.524% / 1.702%|

## 质量与静态资源

124次输出全部finite，A严格相对V29_fast 0bit。B/C三档输出SHA完全一致，相对V29_fast PSNR61.73767/60.82124/59.64497dB，maxabs0.00439453/0.00781250/0.00830078，720天空变号0、HF RMS0.0001053983。这是对已有近似版的新增数值差异，不是原生GPU/F32绝对质量，未做动态游戏视觉验收。

|版本|38核SASS含NOP|不含NOP|PRMT|STL/LDL|
|---|---:|---:|---:|---:|
|baseline|164659|163944|19868|109/104|
|pack8|161832|161111|19862|110/105|
|pack5|152807|152076|19861|107/108|
|pack5_quad|149707|148987|18685|108/111|

所有版本HMMA13188不变。FB04/FB05全部活跃核REG/STACK均未进一步下降；FB01最大STACK仍104B，FB04仍88B，FB00仍16B，其他为0。少PTX临时变量和少静态指令并不保证物理REG更少；逐核完整资源见resources.json。C仅在FB01/02/03融合456/616/616对，共1688对（全导出静态PTX计数）。

## 交付与复现

三份DLL均266414592B，15/15 O4原槽位，无扩节。V27的base_caps/kernel_caps、multidef_nq、lowhigh/lowhigh8、mbarrier不变；A/B mask8，C mask13。
- pack8: `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack8.dll`；SHA256 `9ad5b72d1f2b772cf0a57ccacdcd72dc093874342419ff419a1fc3777e8cbd07`
- pack5: `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5.dll`；SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`
- pack5_quad: `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v31_pack5_quad.dll`；SHA256 `c1a28776b89c09c7e457322de93e0a796e7bd8e7dccaee042e5286e06f3e0fd9`

顺序：check_primitives.py、isolated_sass.py、quad_sass.py、build.py、extract_modules.py、audit.py、run.py；复测repeat.py后analyze.py repeat。复现须使用新的输出目录或归档旧日志（脚本拒绝覆盖计时日志）。代码复用v24融合资格检查，未改变共享生产生成器默认。

保留候选DLL、源码、日志、SASS小核与JSON；清理编译大缓存和RGB。未写本机生产目录、未改发布ZIP、未push。

# Phase17：C32 静态权重追加 FP16，默认采用

基线为Phase16 selected（585fda1），三档输出同时保持Phase14正确gold的既有0bit关系。只改变六个C32核的静态W16矩阵读取；激活、累加顺序、归一化、原量化/RTZ及中间格式不变。外部PTX v0.2.0部署/ZIP不写入。

## 实现与ABI

Host保留原打包缓冲全部字节和偏置/尺度偏移，在尾部追加已Ampere预洗牌的精确FP16：

|缓冲|旧bytes|追加基址|新bytes|解码源区间(byte起点/长度)|
|---|---:|---:|---:|---|
|FFN|41088|41088|60544|2048/4096、18432/4096、34944/1536|
|attention|32900|32912|41104|0/4096（QKV+OutProj）|

FFN包含expand/contract/三段residual diag；attention包含QKV与Attention Out。Host decoder逐bit匹配既有sm86_unpack_e4m3x8，保留负零和subnormal；7f/ff保持现有有限域快捷解释，不扩称IEEE NaN支持。

CUDA后处理仅作用c32-wave1-fast。`cw_half_pair`只保存两个地址，各条MMA在消费点以**ld.global.nc.v4.u32**读对应sm86_u4；volatile/memory约束防止跨循环提前堆积权重。动态输入仍按原方式解包，不将其它站点一并降精度。

目录保留AMPERE_WEIGHTS_V2以配对其余39模块，另加严格内容`AMPERE_WEIGHTS_V3=C32_W16_F16_APPEND_V1`。V3 C32所有entry使用`v3_`命名空间；新Host交叉核验标记/实际导出，旧Host不能误调用同名旧ABI。当前V3支持fast_numeric、W16=1、非temporal；其它C32模式应使用保留的V2模块集，错误组合明确拒绝。

`PHASE17_C32_HALF=True`已成为CUDA构建器默认；完整构建会生成V3标记。运行时按标记自动选择追加布局；显式DLSS5_AMPERE_C32_F16与目录不符会拒绝。仅C32 fast模块变化，其余39个模块SHA与Phase16相同。

## 验收

- Host追加后所有旧字节不变；32768个GPU解码位置覆盖全部256字节模式，GPU新旧解包0bit。
- A/B两侧静态权重、非零C、4次MMA累加共65536个输出元素0bit。
- 六个完整C32 W16核用实际Small权重、相同整幅合成输入独立执行（每核64 CTA），全部输出字节0diff；不称游戏捕获。mapped/up测试最初按half分配了两倍输出，哨兵揭示仅前半写入；按原源码FP8 raw输出修正fixture尺寸后全部写入/比较通过，不涉及生产修改。
- 四项ABI/模式反例均拒绝：V2模块加V3标记、V3模块去标记、V3配W16h、旧Phase16 Host配V3导出。
- 三档初验/ABBA所有输出对冻结Phase16全幅0bit，invalid0、first-last0、32/32活跃核LMem0。
- 最终重建C32及Host，40个模块SHA与实测集合相同；实际加载/resolve40模块1918entry。18项既有Python/LLVM回归通过。

## 正式 ABBA，50warmup /80iter

Small31/Style1、Graph off、默认DVFS，不锁频或改功耗。A=Phase16，B=V3 NC读。每一档顺序A1/B1/B2/A2，单位ms：

|档位|A1 median|B1 median|B2 median|A2 median|两次median均值A→B|速度比|
|---|---:|---:|---:|---:|---:|---:|
|720p|14.067|13.785|13.812|14.066|14.0665→13.7985|1.0194×|
|900p|23.581|23.203|23.215|23.657|23.6190→23.2090|1.0177×|
|1080p|31.608|31.094|31.131|31.828|31.7180→31.1125|1.0195×|

三档两次候选均快于配对基线，约1.8～2.0%速度比，采用V3默认。均值只是简表，不冒充单次帧统计；每次GPU min/median、Wall、独立PROFILE_TOTAL见[results.md](results.md)，六核四次插桩耗时完整见[summary.md](summary.md)。PROFILE_TOTAL不是同一帧median，不能把差额全算launch气泡。原始GPU遥测及按窗口汇总保留，默认DVFS不作等频因果声明。

初始化、上传和最终读回不计入GPU event。首次memcpy向量读取只做了3/5快验，没有作为正式性能控制；最终主候选为NC volatile消费点读取。未用快验时间代替50/80。

## 资源与真实容量

非Up五核仍**8192B Shared /OccW11 /LMem0**，Up仍10240B/OccW9/LMem0。部分寄存器升高、部分下降，不能称全网减半；完整逐核数据见results.md。

六核静态PTX NC v4读取分别prefix/post/mapped/finish/dcrop/up为24/24/24/30/30/24处。SASS HMUL2分别384→224、416→256、368→240、392→232、376→216、424→256；PRMT分别619→459、590→430、534→406、536→376、536→376、615→451。只把它们当静态证据，不换算成动态节省指令量。见isa.json、baseline-resources.txt、candidate-resources.txt。

实际12个C32权重缓冲上传总量 **443928→609888B（+165960B）**，约0.423→0.582MiB；矩阵FP8载荷82944B，新增FP16载荷165888B，另72B对齐填充。全网weights_bytes154793464→154959424，buffer数92不变。原0.39MiB预算不能理解成纯FP8矩阵字节；本实现保留旧区域，新增的是精确读区。

设备查询L2容量4194304B；ncu不可用，未采L1/L2命中率或DRAM流量。容量足够容纳不等于证明100%常驻，不能用这个假设充当提速证据。

## 产物/复测

默认模块入口`phase17/artifacts/selected/modules`（selected是candidate的目录别名，无重复副本）。保留Phase16基线和新模块SHA；selected-modules.sha256.json与measured-modules.sha256.json完全相同。

```bash
python3 Development/hip-port/phase17/build.py
python3 Development/hip-port/phase17/check_primitives.py
python3 Development/hip-port/phase17/check_single_kernels.py
python3 Development/hip-port/phase17/check_abi.py
python3 Development/hip-port/phase17/run_benchmark.py --tag my-retest
python3 Development/hip-port/phase17/check_quality.py
```

新tag防覆盖。Host与模块ABI错配必须先被拒绝，不能手工只拷一个C32模块进旧运行时。summary脚本总结已冻结nc-abba，更多新tag原始记录仍由check_quality收集。

保留最终40模块/PTX/生成源、原始日志、遥测、SHA、GPU/单核与ABI证据；清理重复RGB、单核临时权重和编译中间文件。未改共享assets、v0.2.0游戏/Magpie部署或发布包；独立commit，不push。Phase18不在本轮启动。

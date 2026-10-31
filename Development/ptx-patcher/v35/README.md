# PTX V3.5：Shared FP16 耦合表示的实测闭环

本轮无晋升候选，保留 V3.1_pack5 为唯一 1.00×；分支 4 Pruned 3/3，四个预设分支的 Open=0。

## 构造与正确性

- 固定输入 V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`，baseline 全量 O4 重建同 SHA。所有候选均 266,414,592 B、15/15 O4 原槽位，未改模型、权重、同步或生产文件。
- 原字节 i 对应扩展 FP16 的字节 2i；old u32 的 byte0/1 和 byte2/3 分别成为 first/second f16x2。向量 16B 存取变成两个 16B 存取，原跨 lane/warp 关系保留，不假设同线程。
- FB01 四核的 Shared 写入均可追溯到有限饱和 pack；164 个写端词全部取得对应的 native half 伴随值。FB02/03 的非 pack 原始/混合写入保留旧字节视图，精确 shadow 对任意原字节都使用与基线相同的解码。FB04/05 的 cp.async 别名不作单边扩容。详见 analysis.json、plans.json。
- 独立 shadow：原 Shared 保持，额外 2× payload 专供 MMA 的直接 half 输入；原来 4096B 的 FB01 共用 12288B。原位 inplace：FB01 直接扩成 8192B，非 MMA 的旧字节读取以 pack5 重建，MMA 直接取 half。
- inplace 的安全条件不是“任意字节可逆”：仅对原写端均为有限 pack5 输出的 FB01 启用。GPU 测试确认有限 FP8 解码→pack5 往返与原码一致；7f/ff 保留码不能这样假定。shadow 不需要该限制。
- fast 版保存原始夹断 half；原位 fast 仅改变 MMA 的量化边界，非 MMA 重建旧 pack5 字节。独立/原位 fast 三档输出在快验中相同。其近似性质明确记录，不能称 0-bit。

原语数据见 primitive-tests.json：33,554,432 个字测试中有效有限词共 32,774,128 个，往返 mismatch=0；33,554,432 对 half 夹断后重新 pack5 与原 pack5 一致且不产生 7f/ff；真实 Shared 跨 lane/warp 镜像测试零差异。整网快验与数据检查见 preflight.json / validation.json。

## 预先固定的验收门

精确候选要求同配置末帧 bitdiff=0、maxabs=0、nonfinite=0。fast 候选要求相对 V3.1 三档 PSNR≥50dB、maxabs≤1/64、nonfinite=0、720p 天空变号=0，见 acceptance.json；这是实现间距离，不是原生新卡绝对画质。

## 串行配对结果

首轮 168 次，repeat 0 次；快验 24 次。所有进程串行，构建、GPU 原语与资源查询均先完成。原始每进程输出直接嵌入 bench.json / repeat.json，不生成/提交逐次 .log 碎片。

|轮次/候选|720p 降幅%|900p 降幅%|1080p 降幅%|质量门|
|---|---:|---:|---:|---|
|timed/fb123_exact_shadow|-0.386|-0.619|-0.746|True|
|timed/fb1_exact_inplace|-0.404|-0.682|-0.170|True|
|timed/fb1_exact_shadow|-0.757|-0.319|-0.455|True|
|timed/fb1_fast_inplace|-0.407|0.068|-0.379|True|
|timed/fb1_fast_shadow|-0.136|-0.134|-0.752|True|
|timed/fb2_exact_shadow|-0.291|-0.572|-0.054|True|
|timed/fb3_exact_shadow|0.136|-0.522|0.027|True|

完整正反方向及 PSNR/maxabs 见 timing-summary.md / timing-summary.json。时间是独立进程 GPU median 的均值；默认 DVFS，不混用 min/Wall。首轮三档六方向全胜均补 repeat，晋升还必须两轮质量门都通过。

## 资源与结算

38 个真实活跃 FP8 核的资源与官方 Occupancy API 结果见 resources.json；四张硬件表为 hardware-*.md。循环观察及 Grid 明确沿用已记录账本，没有本轮新硬件 issued/stall 计数。Shared 流量、指令数量和 spill 的变化各自报告，不把某个静态计数直接当成帧收益。

本轮无晋升候选，保留 V3.1_pack5 为唯一 1.00×；分支 4 Pruned 3/3，四个预设分支的 Open=0。

若全部预设分支 Pruned，只表示在本轮明确测试的机制、配置与质量门下未找到晋升项，不能单凭有限 K=3 搜索宣称全局物理极限；可向主脑交接本轮终局材料供其写报告及后续审阅。

生产五处及三 ZIP 的九个保护路径 SHA 不变，不部署、不 push。临时大二进制与逐次日志清理见 cleanup.json；只保留可复核的聚合 JSON/MD 和独立晋升 DLL（若有）。本轮按构造/验证、跑分/硬件表、文档/状态拆成三个提交，无 Co-Authored-By。

全部近似候选正式过程均通过预定质量门，未晋升原因是速度未全档同向；质量汇总见 [quality-summary.md](quality-summary.md)。本轮未进入 repeat，因为首轮无三档六方向全胜项。

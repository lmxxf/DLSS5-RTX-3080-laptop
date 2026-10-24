# LmxxfNrRuntime：让整帧最短的调用顺序（给集成方）

（English: `LmxxfNrApi-call-order.md`。实测见 `Development/results/outside-net-20261002`。）

## 时间花在哪（RX 9070，1080 档，串行测试宿主）

| 段 | 耗时 | 说明 |
|---|---|---|
| `RecordInputs` 的 GPU 活（编码 + RGB 输入） | 约 0.08ms（2026-10-02 起 runtime 直写输入；之前带 35MB 拷贝约 0.21ms） | 在你的队列上 |
| 交接 D3D12 → HIP → D3D12 | 约 0.17～0.28ms | 两条硬件队列间一次 fence 往返，调用顺序消不掉 |
| HIP 网络（`GetTimings`） | 约 9.2ms | |
| `RecordOutputs` 的 GPU 活（neural 纹理 + 解码） | 约 0.11ms | 在你的队列上 |
| CPU：`PrepareFrame` + `Record*` | 约 0.05ms | |
| CPU：`EnqueueHip` | 约 0.3ms | 发约 150 个 HIP 核；你的队列还有活时与 GPU 重叠 |

网络之外 GPU 每帧大约 0.4～0.5ms。如果"网络时间"和"总时间"差好几 ms，那是宿主在等待或 GPU 被别的负载抢占，不是 runtime。

## 推荐顺序（每帧，同一线程）

1. `PrepareFrame`：很便宜。上一帧没 `Retire` 就别调，否则它会在 CPU 上把 GPU 等空。
2. 录你的列表：前置活、`RecordInputs`，关闭。**消费者列表的 `RecordOutputs` 也在这时一起录好**（允许在 `EnqueueHip` 之前录，只是提交必须在它之后），CPU 录制就不在关键路径上。
3. `ExecuteCommandLists(生产者)`。
4. 紧接着在**同一条队列**上 `EnqueueHip`（= `ExecuteAfterProducer`）。中间别插 fence 等待或 `Flush`。
5. `ExecuteCommandLists(消费者)`，随即 `Retire`。`Retire` 不等 GPU。
6. **不要每帧等队列**。保持 2～3 帧在飞，只在复用分配器前等你自己的帧 fence。

## 会变慢的做法

- `EnqueueHip` 用的队列和会话队列不同（开了 `ZERO_OUTPUT_FALLBACK` 时会把两条队列都等空并清零输出）。
- 每帧 `Drain` 或整队列等待（CPU、GPU 串行化；多出 CPU 唤醒延迟约 0.1～0.2ms，再加上全部 CPU 时间）。
- 循环 `Poll`：它只报告 CPU 侧的作业状态（`NR_COMPLETE` 表示"已排队"），从来不是 GPU 完成。
- 为了拿"本帧"而在等完队列后读 `GetTimings`：每帧任意位置读一次即可，非阻塞，返回最新完成的那帧（通常是 N-1）。计时开启本身有一点成本（每帧记 event），不显示就别开。
- 每帧换颜色资源指针 / 尺寸 / 格式或曝光绑定：每次都会重建或重绑编解码链，可能要等 GPU。
- 其他进程的重 GPU 负载：`GetTimings` 本身会变长（例如负载下 1080 档 17ms，空闲约 9.2ms）——那是抢占，不是交接开销。

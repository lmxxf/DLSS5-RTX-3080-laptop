# LmxxfNrRuntime: fastest call order for integrators

(中文版：`LmxxfNrApi-call-order.zh-CN.md`. Measurements: `Development/results/outside-net-20261002`.)

## Where the time goes (RX 9070, 1080 tier, serial test host)

| Segment | Cost | Notes |
|---|---|---|
| `RecordInputs` GPU work (encode + RGB input) | ~0.08 ms (runtime with direct input, after 2026-10-02; was ~0.21 ms with the 35 MB copy) | on your queue |
| Handoff D3D12 → HIP → D3D12 | ~0.17–0.28 ms | one fence round trip between two hardware queues; cannot be removed by call order |
| HIP network (`GetTimings`) | ~9.2 ms | |
| `RecordOutputs` GPU work (neural texture + decode) | ~0.11 ms | on your queue |
| CPU: `PrepareFrame` + `Record*` | ~0.05 ms | |
| CPU: `EnqueueHip` | ~0.3 ms | launches ~150 HIP kernels; overlaps the GPU if your queue still has work |

So outside the network the GPU spends roughly 0.4–0.5 ms per frame. If you see several ms between "network" and "total", it is
host-side waiting or GPU contention, not the runtime.

## Recommended order (per frame, one thread)

1. `PrepareFrame` — cheap. Never call it while the previous job is not `Retire`d: it then drains the GPU on the CPU.
2. Record into your list: your pre-work, `RecordInputs`, close the list. **Record the consumer list with `RecordOutputs` now as well**
   (allowed before `EnqueueHip`; only its submission must come after). This keeps CPU recording off the critical path.
3. `ExecuteCommandLists(producer)`.
4. `EnqueueHip` (= `ExecuteAfterProducer`) on **the same queue** immediately. Do not insert a fence wait or `Flush` here.
5. `ExecuteCommandLists(consumer)`, then `Retire` right away. `Retire` does not wait for the GPU.
6. Do **not** wait for the queue each frame. Keep 2–3 frames in flight and only wait on your own frame fence before reusing allocators.

## Things that make it slow

- A different queue for `EnqueueHip` than the session queue (with `ZERO_OUTPUT_FALLBACK` this drains both queues and zeroes the output).
- `Drain` or a full queue wait every frame (serialises CPU and GPU; adds CPU wake-up latency, ~0.1–0.2 ms, plus all CPU time).
- `Poll` in a loop: it reports the CPU-side job state only (`NR_COMPLETE` means "enqueued"), never GPU completion.
- Reading `GetTimings` after a queue wait just to get "this frame": read it once per frame anywhere; it returns the newest finished
  frame (normally N-1) without blocking. Turning timing on costs a little (events every frame); leave it off in release builds
  unless you display it.
- Changing colour pointer/size/format or exposure binding each frame: each change rebuilds or rebinds the codec chain and may drain.
- Heavy GPU work from other processes: `GetTimings` itself grows (e.g. 17 ms at 1080 under load vs ~9.2 ms idle) — that is
  contention, not handoff overhead.

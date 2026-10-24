# Staged HIP / D3D12 integration

Design inspiration: [TheAutomatic](https://github.com/TheAutomatic), [PR #5](https://github.com/lmxxf/dlss5-on-amd-9070xt-porting/pull/5). This is an independent implementation retaining the existing device, architecture, configuration and diagnostic contracts; the PR was not merged.

## Host sequence

The bridge is single-host-thread, one staged frame at a time. All producer and consumer lists must use the exact queue passed to `Create`, with matching DIRECT/COMPUTE list type and the same D3D12 device. Inputs are RGBA32F buffers in NON_PIXEL_SHADER_RESOURCE; the existing encoder/input stage is responsible for preparing them.

```cpp
// Record into an open host-owned producer list. The bridge never closes it.
bridge.RecordInputCopy(producerList, rgbaBuffer, optionalHistoryBuffer);
// Host closes/submits this producer list to queue here.
bridge.EnqueueAfterProducer(queue, seed, optionalHistoryBuffer != nullptr);
// queue now contains a wait for HIP completion, ahead of subsequently submitted consumers.
bridge.RecordOutputReadable(consumerList);
// Record decode/upscale/other consumers of bridge.Output() on consumerList.
// Host closes/submits consumerList to the same queue here.
bridge.NotifyOutputSubmitted(queue);
```

The consumer may also be recorded immediately after `RecordInputCopy`, before producer submission. This supports hosts that finish recording the whole frame before Execute. Submission order remains producer → EnqueueAfterProducer → consumer → NotifyOutputSubmitted; an early acknowledgement is rejected.

`NotifyOutputSubmitted` acknowledges submission, not GPU completion. It prevents starting another staged frame while the output list has not been acknowledged. The queue order protects input/output reuse, so the CPU need not wait between correctly queued frames. Input buffers, consumer bindings and command allocators must remain alive until their GPU use completes. Do not replay a recorded stage or submit it to another queue.

`WaitForSubmittedWork()` is an explicit teardown wait, returning false if stages are incomplete or work cannot be safely retired. The bridge and `NativeHipNetwork` wrapper retain backing/input references on that failure path. An abandoned recorded list cannot be assumed cancelled; discard the whole integration on error rather than retrying partial work. GPU/API failures poison the bridge. Invalid order, queue or history-flag checks fail before submitting more work.

Staged entry points reject HIP Graph mode **before input recording**. The existing `Run` API continues to support its old Graph path, uses the same internal stages, and supplies its own submission acknowledgements. Existing span/memory/device diagnostics remain available. `NativeHipNetwork` forwards the staged methods using its bound input/history resources.

These methods do not find an insertion point inside an already-recording game list. In RE9 the host still needs a valid producer/consumer submission boundary; this change alone does not move the REFramework post-present path before upscaling or remove its resolution contract.

## Device selection and noise

Typed HIP device properties remain authoritative for LUID matching. Spoofed DXGI VendorId/Description no longer reject an otherwise exact match. Name fallback is allowed only for one AMD-named HIP candidate lacking a LUID. There is no blind single-device fallback. Architecture checks, gfx1200/gfx1201 module-directory selection and public diagnostics are preserved.

`SetNoise({})` is valid only when fast_prefix is enabled; non-fast mode retains the exact table-size requirement. Synchronization/Graph invalidation behavior is retained. `FastPrefixFromEnvironment()` is shared by initialization and the option builder. The normal addon loads flags before deciding whether to load noise, and the RE9 loader makes the same decision. Fast-prefix therefore skips the 201,326,592-byte (192MiB) host table read/allocation; other modes retain it. The noise asset is not removed from packages.

## Per-dispatch codec parameters

```cpp
NativeCodecParameters parameters{detail, colour, NativeCodecDebugView::Final};
codec.Record(commands, inputStates, paperWhite, parameters);
```

Both strengths must be finite and in [0,1]. Debug views: Final, Proxy, Neural (decoded), Difference (20x around grey), Tint. View selection is a per-dispatch root constant, supported across output formats. Existing three-argument calls preserve the cached `DLSS5_STRENGTH` environment behavior and default to Final; explicit values override only that call. Returning to legacy calls restores the legacy strengths. Existing compile/device diagnostics remain enabled and shader compilation failures include compiler text.

The independent codec harness now initializes/binds all 20 root words, including the new debug word; previously it only supplied the first 16.

## Validation

See `tests/bridge-stages` and `../results/bridge-stages-20260922`. Real gfx1201 tests cover 900/1080 output equality, queued frames with distinct seeds, history, legacy Graph, invalid order/queue/history, acknowledgement/retirement, and an injected HIP launch error. Codec tests compare the old shader/class against the new default/legacy/explicit paths, exercise per-frame debug/reset, and validate 44 shader variants. HIP addon, RE9 addon and HLSL compatibility build are compiled. Fullscreen and external multi-GPU/Fake-NVAPI hosts still require their own integration tests.


## Optional exposure and first-frame preparation (RE9)

A host may call `PrepareStagedKernels()` once on a fresh, graph-off bridge before recording input. It enqueues a zero-input warmup and synchronizes, moving lazy weight uploads out of the external-wait submission callback. Normal `Run` callers do not opt in automatically.

The codec can optionally retain a validated 1×1 R16F/R32F exposure texture (t4). With exposure enabled, append its resource state to the `Record` input-state vector. `NativeCodecParameters.pre_exposure` and `.exposure_scale` default to 1; encode normalizes using same-frame GPU exposure and decode restores the original scene units. Nonfinite/nonpositive sampled exposure falls back to 1. Exposure descriptors are preserved in cached colour rebind heaps. Changing the exposure resource requires recreating this codec after GPU completion. Existing no-exposure callers retain their previous results.

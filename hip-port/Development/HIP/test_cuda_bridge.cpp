#include "hip_api.h"
#include <cmath>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

#ifdef _WIN32
#include <d3d12.h>
#include <dxgi1_6.h>
#endif

static const char* kTestPtx = R"(
.version 7.0
.target sm_80
.address_size 64

.visible .global .align 4 .f32 dlss5_style_feature = 0f3B000000;

.visible .entry test_scale_add(
    .param .u64 param_buf,
    .param .u32 param_n
)
{
    .reg .pred %p<2>;
    .reg .b32 %r<5>;
    .reg .f32 %f<5>;
    .reg .b64 %rd<5>;

    ld.param.u64 %rd1, [param_buf];
    ld.param.u32 %r1, [param_n];
    mov.u32 %r2, %ctaid.x;
    mov.u32 %r3, %ntid.x;
    mov.u32 %r4, %tid.x;
    mad.lo.s32 %r2, %r2, %r3, %r4;
    setp.ge.u32 %p1, %r2, %r1;
    @%p1 bra DONE;

    cvta.to.global.u64 %rd2, %rd1;
    mul.wide.u32 %rd3, %r2, 4;
    add.s64 %rd4, %rd2, %rd3;
    ld.global.f32 %f1, [%rd4];
    mov.f32 %f2, 0f40000000; // 2.0f
    mov.f32 %f3, 0f3F800000; // 1.0f
    fma.rn.f32 %f4, %f1, %f2, %f3;
    st.global.f32 [%rd4], %f4;

DONE:
    ret;
}
)";

int main() {
  try {
    hip_probe::Api api(7);
    api.Check(api.hipInit(0), "hipInit");
    int version = 0, count = 0;
    api.Check(api.hipRuntimeGetVersion(&version), "hipRuntimeGetVersion");
    api.Check(api.hipGetDeviceCount(&count), "hipGetDeviceCount");
    std::printf("[CUDA Api] driver_version=%d device_count=%d\n", version, count);
    if (count <= 0) throw std::runtime_error("no CUDA devices found");

    api.Check(api.hipSetDevice(0), "hipSetDevice(0)");
    auto prop = api.Properties(0);
    std::printf("[CUDA Api] device[0] name='%s' arch='%s' sm=%d.%d sram_optin=%zu SMs=%d vram=%.1f MiB\n",
                prop.name, prop.gcnArchName, prop.major, prop.minor,
                prop.sharedMemPerBlockOptin, prop.multiProcessorCount,
                prop.totalGlobalMem / 1048576.0);

    // 1. Test Stream, Events, Allocation, Memcpy, 2D Memcpy, Host Mapped Memory, PTX Kernel Launch
    hip_probe::Handle stream = nullptr, ev0 = nullptr, ev1 = nullptr;
    api.Check(api.hipStreamCreate(&stream), "hipStreamCreate");
    api.Check(api.hipEventCreate(&ev0), "hipEventCreate 0");
    api.Check(api.hipEventCreate(&ev1), "hipEventCreate 1");

    const unsigned N = 1024;
    std::vector<float> host_in(N), host_out(N, 0.0f);
    for (unsigned i = 0; i < N; ++i) host_in[i] = float(i) * 0.25f;

    void* dev_buf = nullptr;
    api.Check(api.hipMalloc(&dev_buf, N * sizeof(float)), "hipMalloc");
    api.Check(api.hipMemcpyAsync(dev_buf, host_in.data(), N * sizeof(float), 1, stream), "hipMemcpyAsync HtoD");

    hip_probe::Handle mod = nullptr, fn = nullptr;
    api.Check(api.hipModuleLoadData(&mod, kTestPtx), "hipModuleLoadData PTX");
    api.Check(api.hipModuleGetFunction(&fn, mod, "test_scale_add"), "hipModuleGetFunction");

    void* gptr = nullptr;
    size_t gsize = 0;
    api.Check(api.hipModuleGetGlobal(&gptr, &gsize, mod, "dlss5_style_feature"), "hipModuleGetGlobal");
    float style_val = 0.5f;
    api.Check(api.hipMemcpy(gptr, &style_val, sizeof(float), 1), "hipMemcpy global");

    api.Check(api.hipEventRecord(ev0, stream), "hipEventRecord start");
    unsigned n_arg = N;
    void* args[] = {&dev_buf, &n_arg};
    api.Check(api.hipModuleLaunchKernel(fn, (N + 255) / 256, 1, 1, 256, 1, 1, 0, stream, args, nullptr),
              "hipModuleLaunchKernel");
    api.Check(api.hipEventRecord(ev1, stream), "hipEventRecord stop");
    api.Check(api.hipMemcpyAsync(host_out.data(), dev_buf, N * sizeof(float), 2, stream), "hipMemcpyAsync DtoH");
    api.Check(api.hipStreamSynchronize(stream), "hipStreamSynchronize");

    float ms = 0.0f;
    api.Check(api.hipEventElapsedTime(&ms, ev0, ev1), "hipEventElapsedTime");
    for (unsigned i = 0; i < N; ++i) {
      float expected = host_in[i] * 2.0f + 1.0f;
      if (std::fabs(host_out[i] - expected) > 1e-5f) {
        throw std::runtime_error("PTX kernel output mismatch at " + std::to_string(i));
      }
    }
    std::printf("[CUDA Api] PTX kernel + global + async copy + events PASS (%.4f ms)\n", ms);

    // 2. Test 2D Strided Memcpy (RGB 12B -> RGBA 16B)
    void *d_rgb = nullptr, *d_rgba = nullptr;
    const size_t pixels = 64;
    api.Check(api.hipMalloc(&d_rgb, pixels * 12), "hipMalloc rgb");
    api.Check(api.hipMalloc(&d_rgba, pixels * 16), "hipMalloc rgba");
    api.Check(api.hipMemsetD32Async(d_rgba, 0x3f800000, pixels * 4, stream), "hipMemsetD32Async alpha=1.0f");
    api.Check(api.hipMemcpyAsync(d_rgb, host_in.data(), pixels * 12, 1, stream), "upload rgb");
    api.Check(api.hipMemcpy2DAsync(d_rgba, 16, d_rgb, 12, 12, pixels, 3, stream), "hipMemcpy2DAsync 12->16");
    std::vector<float> rgba_out(pixels * 4, 0.0f);
    api.Check(api.hipMemcpyAsync(rgba_out.data(), d_rgba, pixels * 16, 2, stream), "download rgba");
    api.Check(api.hipStreamSynchronize(stream), "sync 2D copy");
    for (size_t p = 0; p < pixels; ++p) {
      if (rgba_out[p * 4 + 0] != host_in[p * 3 + 0] ||
          rgba_out[p * 4 + 1] != host_in[p * 3 + 1] ||
          rgba_out[p * 4 + 2] != host_in[p * 3 + 2] ||
          rgba_out[p * 4 + 3] != 1.0f) {
        throw std::runtime_error("2D memcpy mismatch");
      }
    }
    std::printf("[CUDA Api] hipMemcpy2DAsync (12B->16B pitch) + hipMemsetD32Async PASS\n");
    api.hipFree(d_rgb);
    api.hipFree(d_rgba);

#ifdef _WIN32
    // 3. Test D3D12 Adapter LUID matching, External Memory, External Semaphore, and Cross-API PTX Execution
    auto ck = [](HRESULT hr, const char* what) {
      if (FAILED(hr)) throw std::runtime_error(std::string(what) + " hr=" + std::to_string(unsigned(hr)));
    };
    IDXGIFactory4* factory = nullptr;
    ck(CreateDXGIFactory1(IID_PPV_ARGS(&factory)), "CreateDXGIFactory1");
    LUID cuda_luid{};
    std::memcpy(&cuda_luid, prop.luid, 8);
    IDXGIAdapter1* adapter = nullptr;
    ck(factory->EnumAdapterByLuid(cuda_luid, IID_PPV_ARGS(&adapter)), "EnumAdapterByLuid from CUDA LUID");
    DXGI_ADAPTER_DESC1 adesc{};
    adapter->GetDesc1(&adesc);
    char dname[256]{};
    WideCharToMultiByte(CP_UTF8, 0, adesc.Description, -1, dname, 256, nullptr, nullptr);
    std::printf("[D3D12 Bridge] LUID match PASS: D3D12 adapter='%s' LUID=%08x:%08x\n",
                dname, unsigned(adesc.AdapterLuid.HighPart), unsigned(adesc.AdapterLuid.LowPart));

    ID3D12Device* d3d = nullptr;
    ck(D3D12CreateDevice(adapter, D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&d3d)), "D3D12CreateDevice");
    D3D12_COMMAND_QUEUE_DESC qd{};
    qd.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
    ID3D12CommandQueue* queue = nullptr;
    ck(d3d->CreateCommandQueue(&qd, IID_PPV_ARGS(&queue)), "CreateCommandQueue");
    ID3D12CommandAllocator* alloc = nullptr;
    ck(d3d->CreateCommandAllocator(qd.Type, IID_PPV_ARGS(&alloc)), "CreateCommandAllocator");
    ID3D12GraphicsCommandList* cmd = nullptr;
    ck(d3d->CreateCommandList(0, qd.Type, alloc, nullptr, IID_PPV_ARGS(&cmd)), "CreateCommandList");

    const size_t shared_bytes = 65536;
    const unsigned shared_elems = shared_bytes / sizeof(float);
    auto make_buf = [&](D3D12_HEAP_TYPE type, D3D12_HEAP_FLAGS hflags, D3D12_RESOURCE_STATES state) {
      D3D12_HEAP_PROPERTIES hp{};
      hp.Type = type;
      D3D12_RESOURCE_DESC rd{};
      rd.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
      rd.Width = shared_bytes;
      rd.Height = 1;
      rd.DepthOrArraySize = 1;
      rd.MipLevels = 1;
      rd.SampleDesc.Count = 1;
      rd.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
      ID3D12Resource* r = nullptr;
      ck(d3d->CreateCommittedResource(&hp, hflags, &rd, state, nullptr, IID_PPV_ARGS(&r)), "CreateCommittedResource");
      return r;
    };
    ID3D12Resource* upload = make_buf(D3D12_HEAP_TYPE_UPLOAD, D3D12_HEAP_FLAG_NONE, D3D12_RESOURCE_STATE_GENERIC_READ);
    ID3D12Resource* shared = make_buf(D3D12_HEAP_TYPE_DEFAULT, D3D12_HEAP_FLAG_SHARED, D3D12_RESOURCE_STATE_COMMON);
    ID3D12Resource* readback = make_buf(D3D12_HEAP_TYPE_READBACK, D3D12_HEAP_FLAG_NONE, D3D12_RESOURCE_STATE_COPY_DEST);

    HANDLE shared_handle = nullptr;
    ck(d3d->CreateSharedHandle(shared, nullptr, GENERIC_ALL, nullptr, &shared_handle), "CreateSharedHandle buffer");
    D3D12_RESOURCE_DESC srd = shared->GetDesc();
    hip_probe::MemoryDesc md{};
    md.type = 5; // CU_EXTERNAL_MEMORY_HANDLE_TYPE_D3D12_RESOURCE
    md.handle.win32.handle = shared_handle;
    md.size = d3d->GetResourceAllocationInfo(0, 1, &srd).SizeInBytes;
    md.flags = 1; // CUDA_EXTERNAL_MEMORY_DEDICATED
    hip_probe::Handle ext_mem = nullptr;
    api.Check(api.hipImportExternalMemory(&ext_mem, &md), "hipImportExternalMemory");
    hip_probe::BufferDesc bd{};
    bd.size = shared_bytes;
    void* mapped_ptr = nullptr;
    api.Check(api.hipExternalMemoryGetMappedBuffer(&mapped_ptr, ext_mem, &bd), "hipExternalMemoryGetMappedBuffer");

    ID3D12Fence* fence = nullptr;
    ck(d3d->CreateFence(0, D3D12_FENCE_FLAG_SHARED, IID_PPV_ARGS(&fence)), "CreateFence shared");
    HANDLE fence_handle = nullptr;
    ck(d3d->CreateSharedHandle(fence, nullptr, GENERIC_ALL, nullptr, &fence_handle), "CreateSharedHandle fence");
    hip_probe::SemaphoreDesc sd{};
    sd.type = 4; // CU_EXTERNAL_SEMAPHORE_HANDLE_TYPE_D3D12_FENCE
    sd.handle.win32.handle = fence_handle;
    hip_probe::Handle ext_sem = nullptr;
    api.Check(api.hipImportExternalSemaphore(&ext_sem, &sd), "hipImportExternalSemaphore");

    float* up_ptr = nullptr;
    ck(upload->Map(0, nullptr, reinterpret_cast<void**>(&up_ptr)), "Map upload");
    for (unsigned i = 0; i < shared_elems; ++i) up_ptr[i] = float(i) * 0.5f;
    upload->Unmap(0, nullptr);

    cmd->CopyBufferRegion(shared, 0, upload, 0, shared_bytes);
    ck(cmd->Close(), "Close upload cmd");
    ID3D12CommandList* lists[] = {cmd};
    queue->ExecuteCommandLists(1, lists);
    ck(queue->Signal(fence, 1), "D3D12 Signal(1)");

    hip_probe::WaitParams wp{};
    wp.params.fence.value = 1;
    api.Check(api.hipWaitExternalSemaphoresAsync(&ext_sem, &wp, 1, stream), "hipWaitExternalSemaphoresAsync(1)");

    unsigned elems_arg = shared_elems;
    void* kargs[] = {&mapped_ptr, &elems_arg};
    api.Check(api.hipModuleLaunchKernel(fn, (shared_elems + 255) / 256, 1, 1, 256, 1, 1, 0, stream, kargs, nullptr),
              "Launch PTX on D3D12 shared buffer");

    hip_probe::SignalParams sp{};
    sp.params.fence.value = 2;
    api.Check(api.hipSignalExternalSemaphoresAsync(&ext_sem, &sp, 1, stream), "hipSignalExternalSemaphoresAsync(2)");

    ck(queue->Wait(fence, 2), "D3D12 Wait(2)");
    ck(alloc->Reset(), "Reset alloc");
    ck(cmd->Reset(alloc, nullptr), "Reset cmd");
    cmd->CopyBufferRegion(readback, 0, shared, 0, shared_bytes);
    ck(cmd->Close(), "Close readback cmd");
    queue->ExecuteCommandLists(1, lists);
    ck(queue->Signal(fence, 3), "D3D12 Signal(3)");
    HANDLE win_ev = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    ck(fence->SetEventOnCompletion(3, win_ev), "SetEventOnCompletion(3)");
    WaitForSingleObject(win_ev, 10000);

    float* rb_ptr = nullptr;
    ck(readback->Map(0, nullptr, reinterpret_cast<void**>(&rb_ptr)), "Map readback");
    for (unsigned i = 0; i < shared_elems; ++i) {
      float expected = float(i) * 0.5f * 2.0f + 1.0f;
      if (std::fabs(rb_ptr[i] - expected) > 1e-5f) {
        throw std::runtime_error("D3D12 <-> CUDA shared buffer mismatch at " + std::to_string(i));
      }
    }
    readback->Unmap(0, nullptr);
    std::printf("[D3D12 Bridge] D3D12 -> CUDA (PTX Kernel) -> D3D12 Shared Buffer & Fence Interop PASS (%u floats verified)\n",
                shared_elems);

    // Cleanup D3D12 + interop
    api.hipStreamSynchronize(stream);
    api.hipFree(mapped_ptr);
    api.hipDestroyExternalMemory(ext_mem);
    api.hipDestroyExternalSemaphore(ext_sem);
    CloseHandle(shared_handle);
    CloseHandle(fence_handle);
    CloseHandle(win_ev);
    readback->Release();
    shared->Release();
    upload->Release();
    fence->Release();
    cmd->Release();
    alloc->Release();
    queue->Release();
    d3d->Release();
    adapter->Release();
    factory->Release();
#endif

    api.hipModuleUnload(mod);
    api.hipFree(dev_buf);
    api.hipEventDestroy(ev0);
    api.hipEventDestroy(ev1);
    api.hipStreamDestroy(stream);
    std::printf("ALL BRIDGE TESTS PASSED\n");
    return 0;
  } catch (const std::exception& e) {
    std::fprintf(stderr, "TEST FAILED: %s\n", e.what());
    return 1;
  }
}

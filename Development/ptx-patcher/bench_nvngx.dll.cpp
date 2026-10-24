#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <algorithm>
#include <chrono>

static void ck(HRESULT h, const char* k) {
    if (FAILED(h)) {
        printf("D3D_FAIL %s 0x%08x\n", k, unsigned(h));
        fflush(stdout);
        ExitProcess(1);
    }
}

template<class T>
T sym(HMODULE m, const char* n) {
    auto p = GetProcAddress(m, n);
    if (!p) {
        printf("EXPORT_MISSING %s\n", n);
        fflush(stdout);
        ExitProcess(2);
    }
    return reinterpret_cast<T>(p);
}

namespace ngx_abi {
using Result = std::uint32_t;
struct Handle { unsigned Id; };

struct PathListInfo {
    const wchar_t* const* Path;
    unsigned int Length;
};
struct LoggingInfo {
    void (*LoggingCallback)(const char*, int, int);
    int MinimumLoggingLevel;
    bool DisableOtherLoggingSinks;
};
struct FeatureCommonInfo {
    PathListInfo PathListInfo;
    void* InternalData;
    LoggingInfo LoggingInfo;
};

using InitExt = Result(__cdecl*)(unsigned long long, const wchar_t*, ID3D12Device*, unsigned int, const FeatureCommonInfo*);
using GetCaps = Result(__cdecl*)(void**);
using AllocParams = Result(__cdecl*)(void**);
using PopulateParams = Result(__cdecl*)(void*);
using GetScratch = Result(__cdecl*)(unsigned int, const void*, size_t*);
using Create = Result(__cdecl*)(ID3D12GraphicsCommandList*, unsigned int, void*, Handle**);
using Eval = Result(__cdecl*)(ID3D12GraphicsCommandList*, const Handle*, const void*, void*);
using Release = Result(__cdecl*)(Handle*);
using Shutdown1 = Result(__cdecl*)(ID3D12Device*);

inline void** table(void* p) { return *reinterpret_cast<void***>(p); }
inline void SetResource(void* p, const char* k, ID3D12Resource* v) {
    using F = void(__cdecl*)(void*, const char*, ID3D12Resource*);
    reinterpret_cast<F>(table(p)[1])(p, k, v);
}
inline void SetUInt(void* p, const char* k, unsigned v) {
    using F = void(__cdecl*)(void*, const char*, unsigned);
    reinterpret_cast<F>(table(p)[4])(p, k, v);
}
inline void SetFloat(void* p, const char* k, float v) {
    using F = void(__cdecl*)(void*, const char*, float);
    reinterpret_cast<F>(table(p)[6])(p, k, v);
}
inline void SetULL(void* p, const char* k, unsigned long long v) {
    using F = void(__cdecl*)(void*, const char*, unsigned long long);
    reinterpret_cast<F>(table(p)[7])(p, k, v);
}
inline Result GetUInt(void* p, const char* k, unsigned* v) {
    using F = Result(__cdecl*)(void*, const char*, unsigned*);
    return reinterpret_cast<F>(table(p)[12])(p, k, v);
}
inline Result GetFloat(void* p, const char* k, float* v) {
    using F = Result(__cdecl*)(void*, const char*, float*);
    return reinterpret_cast<F>(table(p)[14])(p, k, v);
}
} // namespace ngx_abi

static void log_cb(const char* m, int l, int f) {
    if (std::getenv("NGX_VERBOSE")) {
        printf("NGX[%d][%d] %s", l, f, m);
        if (!m[0] || m[std::strlen(m) - 1] != '\n') putchar('\n');
    }
}

static uint16_t float_to_half(float f) {
    uint32_t x;
    std::memcpy(&x, &f, 4);
    uint32_t sign = (x >> 16) & 0x8000u;
    int32_t exp = ((x >> 23) & 0xff) - 127 + 15;
    uint32_t mant = (x >> 13) & 0x3ffu;
    if (exp <= 0) return uint16_t(sign);
    if (exp >= 31) return uint16_t(sign | 0x7c00u);
    return uint16_t(sign | (uint32_t(exp) << 10) | mant);
}

static float half_to_float(uint16_t h) {
    unsigned e = (h >> 10) & 31, m = h & 1023;
    float v = e == 0 ? std::ldexp(float(m), -24) : e == 31 ? (m ? NAN : INFINITY) : std::ldexp(float(1024 + m), int(e) - 25);
    return (h & 0x8000) ? -v : v;
}

int wmain(int argc, wchar_t** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    if (argc < 6) {
        printf("Usage: %ls <_nvngx.dll> <dlssnr.dll> <width> <height> <preset> [warmup=5] [iters=20] [out.rgb32] [sky]\n", argv[0]);
        return 2;
    }
    const wchar_t* core_path = argv[1];
    const wchar_t* snip_path = argv[2];
    const unsigned W = unsigned(std::wcstoul(argv[3], nullptr, 10));
    const unsigned H = unsigned(std::wcstoul(argv[4], nullptr, 10));
    const unsigned preset = unsigned(std::wcstoul(argv[5], nullptr, 10));
    const unsigned warmup = argc > 6 ? unsigned(std::wcstoul(argv[6], nullptr, 10)) : 5;
    const unsigned iters = argc > 7 ? unsigned(std::wcstoul(argv[7], nullptr, 10)) : 20;
    const wchar_t* out_path = argc > 8 ? argv[8] : nullptr;

    IDXGIFactory4* factory = nullptr;
    ck(CreateDXGIFactory1(IID_PPV_ARGS(&factory)), "factory");
    ID3D12Device* dev = nullptr;
    IDXGIAdapter1* adapter = nullptr;
    for (unsigned i = 0; factory->EnumAdapters1(i, &adapter) != DXGI_ERROR_NOT_FOUND; ++i) {
        DXGI_ADAPTER_DESC1 ad{};
        adapter->GetDesc1(&ad);
        if (ad.VendorId == 0x10de && SUCCEEDED(D3D12CreateDevice(adapter, D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&dev)))) {
            wprintf(L"GPU=%ls (W=%u H=%u preset=%u warmup=%u iters=%u)\n", ad.Description, W, H, preset, warmup, iters);
            break;
        }
        adapter->Release();
        adapter = nullptr;
    }
    if (!dev) {
        puts("NO_NVIDIA_D3D12_DEVICE");
        return 3;
    }

    D3D12_COMMAND_QUEUE_DESC qd{};
    ID3D12CommandQueue* q = nullptr;
    ck(dev->CreateCommandQueue(&qd, IID_PPV_ARGS(&q)), "queue");
    ID3D12CommandAllocator* al = nullptr;
    ID3D12GraphicsCommandList* l = nullptr;
    ck(dev->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&al)), "alloc");
    ck(dev->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, al, nullptr, IID_PPV_ARGS(&l)), "list");

    ID3D12Fence* fe = nullptr;
    ck(dev->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fe)), "fence");
    HANDLE ev = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    UINT64 fv = 0;
    auto wait_gpu = [&]() {
        q->Signal(fe, ++fv);
        fe->SetEventOnCompletion(fv, ev);
        if (WaitForSingleObject(ev, 60000) != WAIT_OBJECT_0) {
            puts("WAIT_TIMEOUT");
            ExitProcess(9);
        }
    };

    // GPU Timestamp Query Heap for exact GPU execution time measurement
    UINT64 ts_freq = 0;
    ck(q->GetTimestampFrequency(&ts_freq), "GetTimestampFrequency");
    D3D12_QUERY_HEAP_DESC qhd{};
    qhd.Type = D3D12_QUERY_HEAP_TYPE_TIMESTAMP;
    qhd.Count = 2;
    ID3D12QueryHeap* qheap = nullptr;
    ck(dev->CreateQueryHeap(&qhd, IID_PPV_ARGS(&qheap)), "CreateQueryHeap");

    auto make_buffer = [&](UINT64 n, D3D12_HEAP_TYPE type) {
        D3D12_HEAP_PROPERTIES hp{};
        hp.Type = type;
        D3D12_RESOURCE_DESC rd{};
        rd.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
        rd.Width = n;
        rd.Height = 1;
        rd.DepthOrArraySize = rd.MipLevels = 1;
        rd.SampleDesc.Count = 1;
        rd.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
        ID3D12Resource* r = nullptr;
        ck(dev->CreateCommittedResource(
            &hp, D3D12_HEAP_FLAG_NONE, &rd,
            type == D3D12_HEAP_TYPE_UPLOAD ? D3D12_RESOURCE_STATE_GENERIC_READ : D3D12_RESOURCE_STATE_COPY_DEST,
            nullptr, IID_PPV_ARGS(&r)), "buffer");
        return r;
    };
    ID3D12Resource* ts_rb = make_buffer(16, D3D12_HEAP_TYPE_READBACK);

    // Load _nvngx.dll just to allocate a genuine NVSDK_NGX_Parameter object
    HMODULE core = LoadLibraryExW(core_path, nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!core) {
        printf("LOAD_CORE_FAIL %lu\n", GetLastError());
        return 4;
    }
    void* p = nullptr;
    auto alloc_fn = reinterpret_cast<ngx_abi::AllocParams>(GetProcAddress(core, "NVSDK_NGX_D3D12_AllocateParameters"));
    if (alloc_fn) {
        auto r = alloc_fn(&p);
        printf("ALLOC_PARAMS=0x%08x params=%p\n", unsigned(r), p);
    }
    if (!p) {
        auto caps_fn = sym<ngx_abi::GetCaps>(core, "NVSDK_NGX_D3D12_GetCapabilityParameters");
        auto r = caps_fn(&p);
        printf("CAPS_PARAMS=0x%08x params=%p\n", unsigned(r), p);
    }
    if (!p) return 5;

    // Now load our patched nvngx_dlssnr.dll directly!
    HMODULE snip = LoadLibraryExW(snip_path, nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!snip) {
        printf("LOAD_SNIP_FAIL %lu\n", GetLastError());
        return 6;
    }
    auto snip_init = sym<ngx_abi::InitExt>(snip, "NVSDK_NGX_D3D12_Init_Ext");
    auto snip_pop = sym<ngx_abi::PopulateParams>(snip, "NVSDK_NGX_D3D12_PopulateParameters_Impl");
    auto snip_scratch = sym<ngx_abi::GetScratch>(snip, "NVSDK_NGX_D3D12_GetScratchBufferSize");
    auto snip_create = sym<ngx_abi::Create>(snip, "NVSDK_NGX_D3D12_CreateFeature");
    auto snip_eval = sym<ngx_abi::Eval>(snip, "NVSDK_NGX_D3D12_EvaluateFeature");
    auto snip_release = sym<ngx_abi::Release>(snip, "NVSDK_NGX_D3D12_ReleaseFeature");
    auto snip_shutdown = sym<ngx_abi::Shutdown1>(snip, "NVSDK_NGX_D3D12_Shutdown1");

    std::wstring snip_dir(snip_path);
    auto slash = snip_dir.find_last_of(L"\\/");
    if (slash != std::wstring::npos) snip_dir.resize(slash);
    const wchar_t* paths[] = { snip_dir.c_str() };
    ngx_abi::FeatureCommonInfo fc{};
    fc.PathListInfo.Path = paths;
    fc.PathListInfo.Length = 1;
    fc.LoggingInfo.LoggingCallback = log_cb;
    fc.LoggingInfo.MinimumLoggingLevel = 3;

    volatile auto r_init = snip_init(0x24480451ull, snip_dir.c_str(), dev, 0x15u, &fc);
    printf("SNIP_INIT=0x%08x\n", unsigned(r_init));
    if (r_init != 1) return 7;

    volatile auto r_pop = snip_pop(p);
    printf("SNIP_POP=0x%08x\n", unsigned(r_pop));

    ngx_abi::SetUInt(p, "DLSSNR.Enabled", 1);
    ngx_abi::SetUInt(p, "DLSSNR.Width", W);
    ngx_abi::SetUInt(p, "DLSSNR.Height", H);
    ngx_abi::SetUInt(p, "Width", W);
    ngx_abi::SetUInt(p, "Height", H);
    ngx_abi::SetUInt(p, "CreationNodeMask", 1);
    ngx_abi::SetUInt(p, "VisibilityNodeMask", 1);
    ngx_abi::SetUInt(p, "DLSSNR.Hint.Render.Preset", preset);
    ngx_abi::SetUInt(p, "DLSSNR.Style", 1);
    ngx_abi::SetFloat(p, "DLSSNR.Intensity", 1.0f);
    ngx_abi::SetFloat(p, "DLSSNR.LocalStructureStrength", 1.0f);
    ngx_abi::SetFloat(p, "DLSSNR.LocalToneStrength", 1.0f);
    ngx_abi::SetFloat(p, "DLSSNR.SkinStructureStrength", -1.0f);
    ngx_abi::SetUInt(p, "DLSSNR.UseAutoMask", 1);
    ngx_abi::SetUInt(p, "DLSSNR.UICorrection", 0);

    size_t scratch_bytes = 0;
    volatile auto r_scr = snip_scratch(18, p, &scratch_bytes);
    printf("SNIP_SCRATCH=0x%08x bytes=%zu\n", unsigned(r_scr), scratch_bytes);

    auto t_create0 = std::chrono::steady_clock::now();
    ngx_abi::Handle* h = nullptr;
    volatile auto r_create = snip_create(l, 18, p, &h);
    printf("SNIP_CREATE18=0x%08x handle=%p\n", unsigned(r_create), h);
    if (r_create != 1) return 8;
    l->Close();
    ID3D12CommandList* ls[] = { l };
    q->ExecuteCommandLists(1, ls);
    wait_gpu();
    double create_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t_create0).count();
    printf("CREATE_DONE_MS=%.2f\n", create_ms);

    auto make_tex = [&](DXGI_FORMAT format, D3D12_RESOURCE_STATES state) {
        D3D12_HEAP_PROPERTIES hp{};
        hp.Type = D3D12_HEAP_TYPE_DEFAULT;
        D3D12_RESOURCE_DESC rd{};
        rd.Dimension = D3D12_RESOURCE_DIMENSION_TEXTURE2D;
        rd.Width = W;
        rd.Height = H;
        rd.DepthOrArraySize = rd.MipLevels = 1;
        rd.SampleDesc.Count = 1;
        rd.Format = format;
        rd.Flags = D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
        ID3D12Resource* r = nullptr;
        ck(dev->CreateCommittedResource(&hp, D3D12_HEAP_FLAG_NONE, &rd, state, nullptr, IID_PPV_ARGS(&r)), "tex");
        return r;
    };

    auto color = make_tex(DXGI_FORMAT_R16G16B16A16_FLOAT, D3D12_RESOURCE_STATE_COPY_DEST);
    auto output = make_tex(DXGI_FORMAT_R16G16B16A16_FLOAT, D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
    auto depth = make_tex(DXGI_FORMAT_R32_FLOAT, D3D12_RESOURCE_STATE_COPY_DEST);
    auto motion = make_tex(DXGI_FORMAT_R16G16_FLOAT, D3D12_RESOURCE_STATE_COPY_DEST);

    auto upload_tex = [&](ID3D12Resource* r, const void* src, size_t bpp) {
        auto rd = r->GetDesc();
        D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};
        UINT64 bytes = 0;
        dev->GetCopyableFootprints(&rd, 0, 1, 0, &fp, nullptr, nullptr, &bytes);
        auto up = make_buffer(bytes, D3D12_HEAP_TYPE_UPLOAD);
        void* dst = nullptr;
        D3D12_RANGE z{ 0, 0 };
        up->Map(0, &z, &dst);
        for (unsigned y = 0; y < H; ++y) {
            std::memcpy(static_cast<char*>(dst) + fp.Offset + size_t(y) * fp.Footprint.RowPitch,
                        static_cast<const char*>(src) + size_t(y) * W * bpp,
                        W * bpp);
        }
        up->Unmap(0, nullptr);
        al->Reset();
        l->Reset(al, nullptr);
        D3D12_TEXTURE_COPY_LOCATION a{}, b{};
        a.pResource = r;
        a.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        b.pResource = up;
        b.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
        b.PlacedFootprint = fp;
        l->CopyTextureRegion(&a, 0, 0, 0, &b, nullptr);
        D3D12_RESOURCE_BARRIER br{};
        br.Transition = { r, D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES, D3D12_RESOURCE_STATE_COPY_DEST, D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE };
        l->ResourceBarrier(1, &br);
        l->Close();
        q->ExecuteCommandLists(1, ls);
        wait_gpu();
        up->Release();
    };

    // Deterministic synthetic HDR scene with smooth gradients + high-frequency detail
    std::vector<uint16_t> color_data(size_t(W) * H * 4);
    std::vector<float> depth_data(size_t(W) * H);
    std::vector<uint32_t> mv_data(size_t(W) * H, 0);
    for (unsigned y = 0; y < H; ++y) {
        for (unsigned x = 0; x < W; ++x) {
            float fx = float(x) / float(W);
            float fy = float(y) / float(H);
            float r = 0.15f + 0.6f * fx + 0.1f * std::sin(fx * 25.0f) * std::cos(fy * 25.0f);
            float g = 0.20f + 0.5f * fy + 0.1f * std::cos(fx * 19.0f + fy * 17.0f);
            float b = 0.25f + 0.4f * (1.0f - fx) + 0.08f * std::sin(fy * 31.0f);
            if (argc > 9 && std::wcscmp(argv[9], L"sky") == 0) {
                // Smooth near-neutral bright sky, spanning the host soft-knee region.
                float v = 0.65f + 0.34f * fy;
                r = v * 0.995f; g = v; b = v * 1.005f;
            }
            size_t idx = (size_t(y) * W + x) * 4;
            color_data[idx + 0] = float_to_half(r);
            color_data[idx + 1] = float_to_half(g);
            color_data[idx + 2] = float_to_half(b);
            color_data[idx + 3] = float_to_half(1.0f);
            depth_data[size_t(y) * W + x] = (argc > 9 && std::wcscmp(argv[9], L"sky") == 0) ? 1.0f : 0.1f + 0.8f * fy;
        }
    }
    upload_tex(color, color_data.data(), 8);
    upload_tex(depth, depth_data.data(), 4);
    upload_tex(motion, mv_data.data(), 4);

    auto setup_eval_params = [&](unsigned reset_flag) {
        ngx_abi::SetUInt(p, "DLSSNR.Enabled", 1);
        ngx_abi::SetUInt(p, "DLSSNR.Width", W);
        ngx_abi::SetUInt(p, "DLSSNR.Height", H);
        ngx_abi::SetUInt(p, "CreationNodeMask", 1);
        ngx_abi::SetUInt(p, "VisibilityNodeMask", 1);
        ngx_abi::SetUInt(p, "DLSSNR.Hint.Render.Preset", preset);
        ngx_abi::SetUInt(p, "DLSSNR.Style", 1);
        ngx_abi::SetFloat(p, "DLSSNR.Intensity", 1.0f);
        ngx_abi::SetFloat(p, "DLSSNR.LocalStructureStrength", 1.0f);
        ngx_abi::SetFloat(p, "DLSSNR.LocalToneStrength", 1.0f);
        ngx_abi::SetFloat(p, "DLSSNR.SkinStructureStrength", -1.0f);
        ngx_abi::SetUInt(p, "DLSSNR.UseAutoMask", 1);
        ngx_abi::SetUInt(p, "DLSSNR.UICorrection", 0);
        ngx_abi::SetResource(p, "DLSSNR.Color", color);
        ngx_abi::SetResource(p, "DLSSNR.Output", output);
        ngx_abi::SetResource(p, "DLSSNR.Depth", depth);
        ngx_abi::SetResource(p, "DLSSNR.MVec", motion);
        ngx_abi::SetUInt(p, "DLSSNR.Reset", reset_flag);
        ngx_abi::SetUInt(p, "DLSSNR.DepthInverted", 0);
        for (const char* k : { "DLSSNR.ColorSubrectBaseX", "DLSSNR.ColorSubrectBaseY",
                               "DLSSNR.OutputSubrectBaseX", "DLSSNR.OutputSubrectBaseY",
                               "DLSSNR.DepthSubrectBaseX", "DLSSNR.DepthSubrectBaseY",
                               "DLSSNR.MVecSubrectBaseX", "DLSSNR.MVecSubrectBaseY" })
            ngx_abi::SetUInt(p, k, 0);
        for (const char* k : { "DLSSNR.ColorSubrectWidth", "DLSSNR.OutputSubrectWidth",
                               "DLSSNR.DepthSubrectWidth", "DLSSNR.MVecSubrectWidth" })
            ngx_abi::SetUInt(p, k, W);
        for (const char* k : { "DLSSNR.ColorSubrectHeight", "DLSSNR.OutputSubrectHeight",
                               "DLSSNR.DepthSubrectHeight", "DLSSNR.MVecSubrectHeight" })
            ngx_abi::SetUInt(p, k, H);
        ngx_abi::SetFloat(p, "DLSSNR.MVecScaleX", 1.0f);
        ngx_abi::SetFloat(p, "DLSSNR.MVecScaleY", 1.0f);
    };

    std::vector<double> gpu_ms_list, wall_ms_list;
    for (unsigned i = 0; i < warmup + iters; ++i) {
        al->Reset();
        l->Reset(al, nullptr);
        setup_eval_params(i == 0 ? 1u : 0u);
        l->EndQuery(qheap, D3D12_QUERY_TYPE_TIMESTAMP, 0);
        auto t0 = std::chrono::steady_clock::now();
        volatile auto er = snip_eval(l, h, p, nullptr);
        if (er != 1) {
            printf("EVAL_FAIL iter=%u res=0x%08x\n", i, unsigned(er));
            return 10;
        }
        l->EndQuery(qheap, D3D12_QUERY_TYPE_TIMESTAMP, 1);
        l->ResolveQueryData(qheap, D3D12_QUERY_TYPE_TIMESTAMP, 0, 2, ts_rb, 0);
        l->Close();
        q->ExecuteCommandLists(1, ls);
        wait_gpu();
        double wall_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();

        uint64_t ts[2] = {};
        void* map = nullptr;
        D3D12_RANGE rr{ 0, 16 };
        ts_rb->Map(0, &rr, &map);
        std::memcpy(ts, map, 16);
        D3D12_RANGE wz{ 0, 0 };
        ts_rb->Unmap(0, &wz);
        double gpu_ms = double(ts[1] - ts[0]) * 1000.0 / double(ts_freq);

        if (i >= warmup) {
            gpu_ms_list.push_back(gpu_ms);
            wall_ms_list.push_back(wall_ms);
        }
    }

    // Readback output to verify finite values and dump if requested
    al->Reset();
    l->Reset(al, nullptr);
    D3D12_RESOURCE_BARRIER b{};
    b.Transition = { output, D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES, D3D12_RESOURCE_STATE_UNORDERED_ACCESS, D3D12_RESOURCE_STATE_COPY_SOURCE };
    l->ResourceBarrier(1, &b);
    auto rd = output->GetDesc();
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};
    UINT64 bytes = 0;
    dev->GetCopyableFootprints(&rd, 0, 1, 0, &fp, nullptr, nullptr, &bytes);
    auto rb = make_buffer(bytes, D3D12_HEAP_TYPE_READBACK);
    D3D12_TEXTURE_COPY_LOCATION loc_dst{}, loc_src{};
    loc_dst.pResource = rb;
    loc_dst.Type = D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;
    loc_dst.PlacedFootprint = fp;
    loc_src.pResource = output;
    loc_src.Type = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
    l->CopyTextureRegion(&loc_dst, 0, 0, 0, &loc_src, nullptr);
    l->Close();
    q->ExecuteCommandLists(1, ls);
    wait_gpu();

    void* map = nullptr;
    D3D12_RANGE rr{ 0, size_t(bytes) };
    rb->Map(0, &rr, &map);
    std::vector<float> rgb(size_t(W) * H * 3);
    size_t nonfinite = 0;
    double sum = 0.0, min_v = 1e30, max_v = -1e30;
    for (size_t y = 0; y < H; ++y) {
        auto row = reinterpret_cast<const uint16_t*>(static_cast<const char*>(map) + fp.Offset + y * fp.Footprint.RowPitch);
        for (size_t x = 0; x < W; ++x) {
            for (size_t c = 0; c < 3; ++c) {
                float v = half_to_float(row[x * 4 + c]);
                rgb[(y * W + x) * 3 + c] = v;
                if (!std::isfinite(v)) {
                    nonfinite++;
                } else {
                    sum += v;
                    min_v = std::min(min_v, double(v));
                    max_v = std::max(max_v, double(v));
                }
            }
        }
    }
    D3D12_RANGE wz{ 0, 0 };
    rb->Unmap(0, &wz);
    rb->Release();

    if (out_path) {
        std::ofstream ofs(out_path, std::ios::binary);
        ofs.write(reinterpret_cast<const char*>(rgb.data()), rgb.size() * sizeof(float));
    }

    std::sort(gpu_ms_list.begin(), gpu_ms_list.end());
    std::sort(wall_ms_list.begin(), wall_ms_list.end());
    double gpu_med = gpu_ms_list[gpu_ms_list.size() / 2];
    double gpu_min = gpu_ms_list.front();
    double gpu_mean = 0;
    for (double v : gpu_ms_list) gpu_mean += v;
    gpu_mean /= gpu_ms_list.size();

    double wall_med = wall_ms_list[wall_ms_list.size() / 2];
    double wall_min = wall_ms_list.front();
    double wall_mean = 0;
    for (double v : wall_ms_list) wall_mean += v;
    wall_mean /= wall_ms_list.size();

    printf("SUMMARY W=%u H=%u preset=%u gpu_median_ms=%.3f gpu_mean_ms=%.3f gpu_min_ms=%.3f wall_median_ms=%.3f wall_mean_ms=%.3f wall_min_ms=%.3f nonfinite=%zu mean_rgb=%.6f range=[%.4f, %.4f]\n",
           W, H, preset, gpu_med, gpu_mean, gpu_min, wall_med, wall_mean, wall_min,
           nonfinite, sum / double(rgb.size()), min_v, max_v);

    volatile auto r_rel = snip_release(h);
    volatile auto r_shut = snip_shutdown(dev);
    (void)r_rel;
    (void)r_shut;
    return nonfinite ? 13 : 0;
}

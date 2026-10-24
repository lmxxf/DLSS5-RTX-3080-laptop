#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
#include <string>

typedef int CUresult;
typedef int CUdevice;
typedef void* CUcontext;
typedef void* CUlinkState;
typedef void* CUmodule;
typedef void* CUfunction;

enum CUjit_option {
    CU_JIT_MAX_REGISTERS = 0,
    CU_JIT_THREADS_PER_BLOCK = 1,
    CU_JIT_WALL_TIME = 2,
    CU_JIT_INFO_LOG_BUFFER = 3,
    CU_JIT_INFO_LOG_BUFFER_SIZE_BYTES = 4,
    CU_JIT_ERROR_LOG_BUFFER = 5,
    CU_JIT_ERROR_LOG_BUFFER_SIZE_BYTES = 6,
    CU_JIT_OPTIMIZATION_LEVEL = 7,
    CU_JIT_TARGET_FROM_CUCONTEXT = 8,
    CU_JIT_TARGET = 9,
    CU_JIT_FALLBACK_STRATEGY = 10,
    CU_JIT_GENERATE_DEBUG_INFO = 11,
    CU_JIT_LOG_VERBOSE = 12,
    CU_JIT_GENERATE_LINE_INFO = 13,
    CU_JIT_CACHE_MODE = 14
};

enum CUjitInputType {
    CU_JIT_INPUT_CUBIN = 0,
    CU_JIT_INPUT_PTX = 1,
    CU_JIT_INPUT_FATBINARY = 2,
    CU_JIT_INPUT_OBJECT = 3,
    CU_JIT_INPUT_LIBRARY = 4
};

extern "C" {
    CUresult cuInit(unsigned int Flags);
    CUresult cuDeviceGet(CUdevice* device, int ordinal);
    CUresult cuDeviceGetName(char* name, int len, CUdevice dev);
    CUresult cuCtxCreate_v2(CUcontext* pctx, unsigned int flags, CUdevice dev);
    CUresult cuCtxDestroy_v2(CUcontext ctx);
    CUresult cuLinkCreate_v2(unsigned int numOptions, CUjit_option* options, void** optionValues, CUlinkState* stateOut);
    CUresult cuLinkAddData_v2(CUlinkState state, CUjitInputType type, void* data, size_t size, const char* name,
                              unsigned int numOptions, CUjit_option* options, void** optionValues);
    CUresult cuLinkComplete(CUlinkState state, void** cubinOut, size_t* sizeOut);
    CUresult cuLinkDestroy(CUlinkState state);
    CUresult cuModuleLoadData(CUmodule* module, const void* image);
    CUresult cuModuleGetFunction(CUfunction* hfunc, CUmodule hmod, const char* name);
    CUresult cuModuleUnload(CUmodule hmod);
}

#define CHECK_CU(call, msg) do { \
    CUresult r = (call); \
    if (r != 0) { \
        fprintf(stderr, "CUDA Error %d at %s\n", r, msg); \
        return 1; \
    } \
} while(0)

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input.ptx> <output.cubin> [func_to_verify ...]\n", argv[0]);
        return 2;
    }
    std::ifstream ifs(argv[1], std::ios::binary);
    if (!ifs) {
        fprintf(stderr, "Cannot open PTX file: %s\n", argv[1]);
        return 1;
    }
    std::string ptx((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
    ptx.push_back('\0');

    CHECK_CU(cuInit(0), "cuInit");
    CUdevice dev = 0;
    CHECK_CU(cuDeviceGet(&dev, 0), "cuDeviceGet");
    char devName[128] = {};
    cuDeviceGetName(devName, sizeof(devName), dev);

    CUcontext ctx = nullptr;
    CHECK_CU(cuCtxCreate_v2(&ctx, 0, dev), "cuCtxCreate");

    char infoLog[16384] = {};
    char errLog[16384] = {};
    CUjit_option opts[] = {
        CU_JIT_INFO_LOG_BUFFER,
        CU_JIT_INFO_LOG_BUFFER_SIZE_BYTES,
        CU_JIT_ERROR_LOG_BUFFER,
        CU_JIT_ERROR_LOG_BUFFER_SIZE_BYTES,
        CU_JIT_OPTIMIZATION_LEVEL,
        CU_JIT_TARGET
    };
    void* optVals[] = {
        infoLog,
        (void*)(uintptr_t)sizeof(infoLog),
        errLog,
        (void*)(uintptr_t)sizeof(errLog),
        (void*)(uintptr_t)4,
        (void*)(uintptr_t)86 // CU_TARGET_COMPUTE_86 = 86
    };

    CUlinkState linkState = nullptr;
    CHECK_CU(cuLinkCreate_v2(6, opts, optVals, &linkState), "cuLinkCreate");

    CUresult r = cuLinkAddData_v2(linkState, CU_JIT_INPUT_PTX, (void*)ptx.data(), ptx.size() - 1, argv[1], 0, nullptr, nullptr);
    if (r != 0) {
        fprintf(stderr, "cuLinkAddData failed (%d):\n%s\n", r, errLog);
        return 1;
    }

    void* cubin = nullptr;
    size_t cubinSize = 0;
    r = cuLinkComplete(linkState, &cubin, &cubinSize);
    if (r != 0) {
        fprintf(stderr, "cuLinkComplete failed (%d):\n%s\n", r, errLog);
        return 1;
    }

    std::ofstream ofs(argv[2], std::ios::binary);
    ofs.write((const char*)cubin, cubinSize);
    ofs.close();

    CUmodule mod = nullptr;
    CHECK_CU(cuModuleLoadData(&mod, cubin), "cuModuleLoadData");
    for (int i = 3; i < argc; ++i) {
        CUfunction fn = nullptr;
        CHECK_CU(cuModuleGetFunction(&fn, mod, argv[i]), argv[i]);
    }
    cuModuleUnload(mod);
    cuLinkDestroy(linkState);
    cuCtxDestroy_v2(ctx);
    return 0;
}

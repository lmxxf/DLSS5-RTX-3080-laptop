#pragma once
// Drop-in NVIDIA CUDA Driver API (nvcuda.dll / libcuda.so.1) backend for the hip_probe::Api ABI.
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <dlfcn.h>
using HMODULE = void*;
inline void OutputDebugStringA(const char*) {}
inline short GetAsyncKeyState(int) { return 0; }
#ifndef VK_F8
#define VK_F8 0x77
#endif
#endif

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>
#include "hip_device_properties.h"

namespace hip_probe {
using Handle = void*;
using CUdeviceptr = unsigned long long;
using CUdevice = int;

struct MemoryDesc {
  int type;
  union {
    int fd;
    struct {
      void* handle;
      const void* name;
    } win32;
    const void* nvSciBufObject;
  } handle;
  unsigned long long size;
  unsigned flags;
  unsigned reserved[16];
};
struct BufferDesc {
  unsigned long long offset, size;
  unsigned flags;
  unsigned reserved[16];
};
struct SemaphoreDesc {
  int type;
  union {
    int fd;
    struct {
      void* handle;
      const void* name;
    } win32;
    const void* nvSciSyncObj;
  } handle;
  unsigned flags;
  unsigned reserved[16];
};
struct SignalParams {
  struct {
    struct {
      unsigned long long value;
    } fence;
    union {
      void* fence;
      unsigned long long reserved;
    } nvSciSync;
    struct {
      unsigned long long key;
    } keyedMutex;
    unsigned reserved[12];
  } params;
  unsigned flags;
  unsigned reserved[16];
};
struct WaitParams {
  struct {
    struct {
      unsigned long long value;
    } fence;
    union {
      void* fence;
      unsigned long long reserved;
    } nvSciSync;
    struct {
      unsigned long long key;
      unsigned timeoutMs;
    } keyedMutex;
    unsigned reserved[10];
  } params;
  unsigned flags;
  unsigned reserved[16];
};
// Virtual memory management: matches CUmemAllocationProp_v1 (88 bytes on x64) and CUmemAccessDesc_v1.
struct MemAllocationProp {
  unsigned type;
  unsigned requestedHandleType;
  struct {
    unsigned type;
    int id;
  } location;
  void* win32HandleMetaData;
  struct {
    unsigned char compressionType, gpuDirectRDMACapable;
    unsigned short usage;
    unsigned char reserved[4];
    unsigned char cuda_reserved[56];
  } allocFlags;
};
struct MemAccessDesc {
  struct {
    unsigned type;
    int id;
  } location;
  unsigned flags;
};
static_assert(sizeof(MemoryDesc) == 104 && sizeof(BufferDesc) == 88 &&
                  sizeof(SemaphoreDesc) == 96 && sizeof(SignalParams) == 144 &&
                  sizeof(WaitParams) == 144,
              "CUDA/HIP external resource ABI");

struct CudaMemcpy2DDesc {
  size_t srcXInBytes;
  size_t srcY;
  int srcMemoryType;
  const void* srcHost;
  CUdeviceptr srcDevice;
  void* srcArray;
  size_t srcPitch;
  size_t dstXInBytes;
  size_t dstY;
  int dstMemoryType;
  void* dstHost;
  CUdeviceptr dstDevice;
  void* dstArray;
  size_t dstPitch;
  size_t WidthInBytes;
  size_t Height;
};

namespace detail {
inline void* RawSym(HMODULE dll, const char* name) noexcept {
  if (!dll || !name) return nullptr;
#ifdef _WIN32
  return reinterpret_cast<void*>(GetProcAddress(dll, name));
#else
  return dlsym(dll, name);
#endif
}

struct CudaDriver {
  HMODULE dll{};
  std::mutex ctx_mutex;
  Handle device_ctxs[16]{};
  std::atomic<int> active_device{0};
  std::mutex fn_mutex;
  std::vector<std::pair<Handle, std::string>> fn_names;

  const char* LookupFnName(Handle f) {
    std::lock_guard<std::mutex> lock(fn_mutex);
    for (const auto& kv : fn_names) {
      if (kv.first == f) return kv.second.c_str();
    }
    return "<unknown>";
  }

  int (*cuInit)(unsigned){};
  int (*cuDriverGetVersion)(int*){};
  int (*cuDeviceGetCount)(int*){};
  int (*cuDeviceGet)(CUdevice*, int){};
  int (*cuDeviceGetName)(char*, int, CUdevice){};
  int (*cuDeviceTotalMem_v2)(size_t*, CUdevice){};
  int (*cuDeviceGetAttribute)(int*, int, CUdevice){};
  int (*cuDeviceGetUuid)(hipUUID*, CUdevice){};
  int (*cuDeviceGetLuid)(char*, unsigned int*, CUdevice){};
  int (*cuDevicePrimaryCtxRetain)(Handle*, CUdevice){};
  int (*cuCtxSetCurrent)(Handle){};
  int (*cuCtxGetCurrent)(Handle*){};
  int (*cuCtxSynchronize)(){};

  int (*cuMemGetInfo_v2)(size_t*, size_t*){};
  int (*cuMemAlloc_v2)(CUdeviceptr*, size_t){};
  int (*cuMemFree_v2)(CUdeviceptr){};
  int (*cuMemHostAlloc)(void**, size_t, unsigned){};
  int (*cuMemFreeHost)(void*){};
  int (*cuMemHostGetDevicePointer_v2)(CUdeviceptr*, void*, unsigned){};
  int (*cuMemcpy)(CUdeviceptr, CUdeviceptr, size_t){};
  int (*cuMemcpyHtoD_v2)(CUdeviceptr, const void*, size_t){};
  int (*cuMemcpyDtoH_v2)(void*, CUdeviceptr, size_t){};
  int (*cuMemcpyDtoD_v2)(CUdeviceptr, CUdeviceptr, size_t){};
  int (*cuMemcpyAsync)(CUdeviceptr, CUdeviceptr, size_t, Handle){};
  int (*cuMemcpyHtoDAsync_v2)(CUdeviceptr, const void*, size_t, Handle){};
  int (*cuMemcpyDtoHAsync_v2)(void*, CUdeviceptr, size_t, Handle){};
  int (*cuMemcpyDtoDAsync_v2)(CUdeviceptr, CUdeviceptr, size_t, Handle){};
  int (*cuMemcpy2DAsync_v2)(const CudaMemcpy2DDesc*, Handle){};
  int (*cuMemsetD8Async)(CUdeviceptr, unsigned char, size_t, Handle){};
  int (*cuMemsetD32Async)(CUdeviceptr, unsigned, size_t, Handle){};

  int (*cuEventCreate)(Handle*, unsigned){};
  int (*cuEventRecord)(Handle, Handle){};
  int (*cuEventElapsedTime)(float*, Handle, Handle){};
  int (*cuEventDestroy_v2)(Handle){};
  int (*cuEventSynchronize)(Handle){};
  int (*cuEventQuery)(Handle){};

  int (*cuStreamCreate)(Handle*, unsigned){};
  int (*cuStreamSynchronize)(Handle){};
  int (*cuStreamDestroy_v2)(Handle){};
  int (*cuStreamQuery)(Handle){};
  int (*cuStreamWaitValue32_v2)(Handle, CUdeviceptr, unsigned, unsigned){};

  int (*cuImportExternalMemory)(Handle*, const MemoryDesc*){};
  int (*cuExternalMemoryGetMappedBuffer)(CUdeviceptr*, Handle, const BufferDesc*){};
  int (*cuDestroyExternalMemory)(Handle){};
  int (*cuImportExternalSemaphore)(Handle*, const SemaphoreDesc*){};
  int (*cuSignalExternalSemaphoresAsync)(const Handle*, const SignalParams*, unsigned, Handle){};
  int (*cuWaitExternalSemaphoresAsync)(const Handle*, const WaitParams*, unsigned, Handle){};
  int (*cuDestroyExternalSemaphore)(Handle){};

  int (*cuStreamBeginCapture_v2)(Handle, int){};
  int (*cuStreamEndCapture)(Handle, Handle*){};
  int (*cuGraphInstantiateWithFlags)(Handle*, Handle, unsigned long long){};
  int (*cuGraphInstantiate_v2)(Handle*, Handle, Handle*, char*, size_t){};
  int (*cuGraphLaunch)(Handle, Handle){};
  int (*cuGraphDestroy)(Handle){};
  int (*cuGraphExecDestroy)(Handle){};

  int (*cuMemAddressReserve)(CUdeviceptr*, size_t, size_t, CUdeviceptr, unsigned long long){};
  int (*cuMemAddressFree)(CUdeviceptr, size_t){};
  int (*cuMemCreate)(Handle*, size_t, const MemAllocationProp*, unsigned long long){};
  int (*cuMemRelease)(Handle){};
  int (*cuMemMap)(CUdeviceptr, size_t, size_t, Handle, unsigned long long){};
  int (*cuMemUnmap)(CUdeviceptr, size_t){};
  int (*cuMemSetAccess)(CUdeviceptr, size_t, const MemAccessDesc*, size_t){};
  int (*cuMemGetAllocationGranularity)(size_t*, const MemAllocationProp*, int){};

  int (*cuModuleLoad)(Handle*, const char*){};
  int (*cuModuleLoadData)(Handle*, const void*){};
  int (*cuModuleGetFunction)(Handle*, Handle, const char*){};
  int (*cuModuleGetGlobal_v2)(CUdeviceptr*, size_t*, Handle, const char*){};
  int (*cuModuleUnload)(Handle){};
  int (*cuLaunchKernel)(Handle, unsigned, unsigned, unsigned, unsigned, unsigned, unsigned, unsigned, Handle, void**, void**){};
  int (*cuFuncGetAttribute)(int*, int, Handle){};
  int (*cuFuncSetAttribute)(Handle, int, int){};
  int (*cuGetErrorName)(int, const char**){};

  template <class T>
  void Req(T& fn, const char* name) {
    fn = reinterpret_cast<T>(RawSym(dll, name));
    if (!fn) throw std::runtime_error(std::string("missing CUDA driver export ") + name);
  }
  template <class T>
  void Opt(T& fn, const char* name) noexcept {
    fn = reinterpret_cast<T>(RawSym(dll, name));
  }

  CudaDriver() {
#ifdef _WIN32
    dll = LoadLibraryExW(L"nvcuda.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!dll) dll = LoadLibraryW(L"nvcuda.dll");
    if (!dll) throw std::runtime_error("NVIDIA CUDA driver (nvcuda.dll) not found in System32");
#else
    dll = dlopen("libcuda.so.1", RTLD_NOW);
    if (!dll) dll = dlopen("/usr/lib/wsl/lib/libcuda.so.1", RTLD_NOW);
    if (!dll) throw std::runtime_error("NVIDIA CUDA driver (libcuda.so.1) not found");
#endif
    Req(cuInit, "cuInit");
    Req(cuDriverGetVersion, "cuDriverGetVersion");
    Req(cuDeviceGetCount, "cuDeviceGetCount");
    Req(cuDeviceGet, "cuDeviceGet");
    Req(cuDeviceGetName, "cuDeviceGetName");
    Req(cuDeviceTotalMem_v2, "cuDeviceTotalMem_v2");
    Req(cuDeviceGetAttribute, "cuDeviceGetAttribute");
    Req(cuDeviceGetUuid, "cuDeviceGetUuid");
    Opt(cuDeviceGetLuid, "cuDeviceGetLuid");
    Req(cuDevicePrimaryCtxRetain, "cuDevicePrimaryCtxRetain");
    Req(cuCtxSetCurrent, "cuCtxSetCurrent");
    Req(cuCtxGetCurrent, "cuCtxGetCurrent");
    Req(cuCtxSynchronize, "cuCtxSynchronize");

    Req(cuMemGetInfo_v2, "cuMemGetInfo_v2");
    Req(cuMemAlloc_v2, "cuMemAlloc_v2");
    Req(cuMemFree_v2, "cuMemFree_v2");
    Req(cuMemHostAlloc, "cuMemHostAlloc");
    Req(cuMemFreeHost, "cuMemFreeHost");
    Req(cuMemHostGetDevicePointer_v2, "cuMemHostGetDevicePointer_v2");
    Req(cuMemcpy, "cuMemcpy");
    Req(cuMemcpyHtoD_v2, "cuMemcpyHtoD_v2");
    Req(cuMemcpyDtoH_v2, "cuMemcpyDtoH_v2");
    Req(cuMemcpyDtoD_v2, "cuMemcpyDtoD_v2");
    Req(cuMemcpyAsync, "cuMemcpyAsync");
    Req(cuMemcpyHtoDAsync_v2, "cuMemcpyHtoDAsync_v2");
    Req(cuMemcpyDtoHAsync_v2, "cuMemcpyDtoHAsync_v2");
    Req(cuMemcpyDtoDAsync_v2, "cuMemcpyDtoDAsync_v2");
    Req(cuMemcpy2DAsync_v2, "cuMemcpy2DAsync_v2");
    Req(cuMemsetD8Async, "cuMemsetD8Async");
    Req(cuMemsetD32Async, "cuMemsetD32Async");

    Req(cuEventCreate, "cuEventCreate");
    Req(cuEventRecord, "cuEventRecord");
    Req(cuEventElapsedTime, "cuEventElapsedTime");
    Req(cuEventDestroy_v2, "cuEventDestroy_v2");
    Req(cuEventSynchronize, "cuEventSynchronize");
    Req(cuEventQuery, "cuEventQuery");

    Req(cuStreamCreate, "cuStreamCreate");
    Req(cuStreamSynchronize, "cuStreamSynchronize");
    Req(cuStreamDestroy_v2, "cuStreamDestroy_v2");
    Req(cuStreamQuery, "cuStreamQuery");
    Opt(cuStreamWaitValue32_v2, "cuStreamWaitValue32_v2");

    Req(cuImportExternalMemory, "cuImportExternalMemory");
    Req(cuExternalMemoryGetMappedBuffer, "cuExternalMemoryGetMappedBuffer");
    Req(cuDestroyExternalMemory, "cuDestroyExternalMemory");
    Req(cuImportExternalSemaphore, "cuImportExternalSemaphore");
    Req(cuSignalExternalSemaphoresAsync, "cuSignalExternalSemaphoresAsync");
    Req(cuWaitExternalSemaphoresAsync, "cuWaitExternalSemaphoresAsync");
    Req(cuDestroyExternalSemaphore, "cuDestroyExternalSemaphore");

    Opt(cuStreamBeginCapture_v2, "cuStreamBeginCapture_v2");
    Opt(cuStreamEndCapture, "cuStreamEndCapture");
    Opt(cuGraphInstantiateWithFlags, "cuGraphInstantiateWithFlags");
    Opt(cuGraphInstantiate_v2, "cuGraphInstantiate_v2");
    Opt(cuGraphLaunch, "cuGraphLaunch");
    Opt(cuGraphDestroy, "cuGraphDestroy");
    Opt(cuGraphExecDestroy, "cuGraphExecDestroy");

    Opt(cuMemAddressReserve, "cuMemAddressReserve");
    Opt(cuMemAddressFree, "cuMemAddressFree");
    Opt(cuMemCreate, "cuMemCreate");
    Opt(cuMemRelease, "cuMemRelease");
    Opt(cuMemMap, "cuMemMap");
    Opt(cuMemUnmap, "cuMemUnmap");
    Opt(cuMemSetAccess, "cuMemSetAccess");
    Opt(cuMemGetAllocationGranularity, "cuMemGetAllocationGranularity");

    Req(cuModuleLoad, "cuModuleLoad");
    Req(cuModuleLoadData, "cuModuleLoadData");
    Req(cuModuleGetFunction, "cuModuleGetFunction");
    Req(cuModuleGetGlobal_v2, "cuModuleGetGlobal_v2");
    Req(cuModuleUnload, "cuModuleUnload");
    Req(cuLaunchKernel, "cuLaunchKernel");
    Opt(cuFuncGetAttribute, "cuFuncGetAttribute");
    Opt(cuFuncSetAttribute, "cuFuncSetAttribute");
    Req(cuGetErrorName, "cuGetErrorName");
  }
};

inline CudaDriver& Drv() {
  static CudaDriver d;
  return d;
}

inline Handle& ThreadBoundCtx() noexcept {
  static thread_local Handle ctx = nullptr;
  return ctx;
}

inline int BindDeviceContext(int device) noexcept {
  if (device < 0 || device >= 16) return 101;
  auto& d = Drv();
  Handle ctx = nullptr;
  {
    std::lock_guard<std::mutex> lock(d.ctx_mutex);
    ctx = d.device_ctxs[device];
    if (!ctx) {
      CUdevice cuDev = 0;
      int r = d.cuDeviceGet(&cuDev, device);
      if (r) return r;
      r = d.cuDevicePrimaryCtxRetain(&ctx, cuDev);
      if (r) return r;
      d.device_ctxs[device] = ctx;
    }
  }
  int r = d.cuCtxSetCurrent(ctx);
  if (r == 0) {
    ThreadBoundCtx() = ctx;
    d.active_device.store(device, std::memory_order_relaxed);
  }
  return r;
}

inline int EnsureCurrentContext() noexcept {
  if (ThreadBoundCtx()) return 0;
  auto& d = Drv();
  Handle cur = nullptr;
  if (d.cuCtxGetCurrent(&cur) == 0 && cur != nullptr) {
    ThreadBoundCtx() = cur;
    return 0;
  }
  return BindDeviceContext(d.active_device.load(std::memory_order_relaxed));
}

inline std::filesystem::path ResolveModuleFile(const char* path) {
  std::filesystem::path p = std::filesystem::u8path(path ? path : "");
  if (p.extension() == ".hsaco") {
    auto cubin = p;
    cubin.replace_extension(".cubin");
    if (std::filesystem::exists(cubin)) return cubin;
    if (std::filesystem::exists(p)) {
      // Check if the .hsaco file is an AMDGPU ELF (e_machine == 224); if so, prefer .ptx if present.
      std::ifstream f(p, std::ios::binary);
      unsigned char hdr[20]{};
      if (f.read(reinterpret_cast<char*>(hdr), 20)) {
        uint16_t e_machine = static_cast<uint16_t>(hdr[18] | (hdr[19] << 8));
        if (hdr[0] == 0x7f && hdr[1] == 'E' && hdr[2] == 'L' && hdr[3] == 'F' && e_machine == 224) {
          auto ptx = p;
          ptx.replace_extension(".ptx");
          if (std::filesystem::exists(ptx)) return ptx;
        }
      }
      return p;
    }
    auto ptx = p;
    ptx.replace_extension(".ptx");
    if (std::filesystem::exists(ptx)) return ptx;
  }
  return p;
}

inline int WrapHipInit(unsigned flags) noexcept {
  auto& d = Drv();
  int r = d.cuInit(flags);
  if (r) return r;
  int count = 0;
  if (d.cuDeviceGetCount(&count) == 0 && count > 0) {
    Handle cur = nullptr;
    if (d.cuCtxGetCurrent(&cur) != 0 || !cur) {
      BindDeviceContext(0);
    }
  }
  return 0;
}

inline int WrapHipRuntimeGetVersion(int* version) noexcept {
  return Drv().cuDriverGetVersion(version);
}

inline int WrapHipGetDeviceCount(int* count) noexcept {
  return Drv().cuDeviceGetCount(count);
}

inline int WrapHipDeviceGetName(char* name, int len, int device) noexcept {
  auto& d = Drv();
  CUdevice cuDev = 0;
  int r = d.cuDeviceGet(&cuDev, device);
  if (r) return r;
  return d.cuDeviceGetName(name, len, cuDev);
}

inline int WrapHipSetDevice(int device) noexcept {
  return BindDeviceContext(device);
}

inline int WrapHipGetDevicePropertiesR0600(DevicePropertiesR0600* prop, int device) noexcept {
  if (!prop) return 1;
  std::memset(prop, 0, sizeof(*prop));
  auto& d = Drv();
  CUdevice cuDev = 0;
  int r = d.cuDeviceGet(&cuDev, device);
  if (r) return r;
  r = d.cuDeviceGetName(prop->name, sizeof(prop->name), cuDev);
  if (r) return r;
  d.cuDeviceTotalMem_v2(&prop->totalGlobalMem, cuDev);
  d.cuDeviceGetUuid(&prop->uuid, cuDev);
  if (d.cuDeviceGetLuid) {
    d.cuDeviceGetLuid(prop->luid, &prop->luidDeviceNodeMask, cuDev);
  }
  auto attr = [&](int code) -> int {
    int val = 0;
    d.cuDeviceGetAttribute(&val, code, cuDev);
    return val;
  };
  prop->maxThreadsPerBlock = attr(1);
  prop->maxThreadsDim[0] = attr(2);
  prop->maxThreadsDim[1] = attr(3);
  prop->maxThreadsDim[2] = attr(4);
  prop->maxGridSize[0] = attr(5);
  prop->maxGridSize[1] = attr(6);
  prop->maxGridSize[2] = attr(7);
  prop->sharedMemPerBlock = static_cast<size_t>(attr(8));
  prop->totalConstMem = static_cast<size_t>(attr(9));
  prop->warpSize = attr(10);
  prop->regsPerBlock = attr(12);
  prop->clockRate = attr(13);
  prop->multiProcessorCount = attr(16);
  prop->integrated = attr(18);
  prop->canMapHostMemory = attr(19);
  prop->computeMode = attr(20);
  prop->concurrentKernels = attr(31);
  prop->pciBusID = attr(33);
  prop->pciDeviceID = attr(34);
  prop->memoryClockRate = attr(36);
  prop->memoryBusWidth = attr(37);
  prop->l2CacheSize = attr(38);
  prop->maxThreadsPerMultiProcessor = attr(39);
  prop->unifiedAddressing = attr(41);
  prop->pciDomainID = attr(50);
  prop->major = attr(75);
  prop->minor = attr(76);
  prop->sharedMemPerMultiprocessor = static_cast<size_t>(attr(81));
  prop->maxSharedMemoryPerMultiProcessor = prop->sharedMemPerMultiprocessor;
  prop->regsPerMultiprocessor = attr(82);
  prop->managedMemory = attr(83);
  prop->sharedMemPerBlockOptin = static_cast<size_t>(attr(97));
  if (const char* arch_override = std::getenv("DLSS5_CUDA_ARCH_NAME"); arch_override && *arch_override) {
    std::snprintf(prop->gcnArchName, sizeof(prop->gcnArchName), "%s", arch_override);
  } else {
    std::snprintf(prop->gcnArchName, sizeof(prop->gcnArchName), "gfx1201");
  }
  return 0;
}

inline int WrapHipMemGetInfo(size_t* free_bytes, size_t* total_bytes) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuMemGetInfo_v2(free_bytes, total_bytes);
}

inline int WrapHipMalloc(void** ptr, size_t bytes) noexcept {
  if (!ptr) return 1;
  *ptr = nullptr;
  if (bytes == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  CUdeviceptr dptr = 0;
  r = Drv().cuMemAlloc_v2(&dptr, bytes);
  if (r == 0) *ptr = reinterpret_cast<void*>(static_cast<uintptr_t>(dptr));
  return r;
}

inline int WrapHipFree(void* ptr) noexcept {
  if (!ptr) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuMemFree_v2(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)));
}

inline int WrapHipHostMalloc(void** ptr, size_t bytes, unsigned flags) noexcept {
  (void)flags;
  if (!ptr) return 1;
  *ptr = nullptr;
  int r = EnsureCurrentContext();
  if (r) return r;
  // CU_MEMHOSTALLOC_PORTABLE (1) | CU_MEMHOSTALLOC_DEVICEMAP (2)
  return Drv().cuMemHostAlloc(ptr, bytes, 1u | 2u);
}

inline int WrapHipHostGetDevicePointer(void** dev_ptr, void* host_ptr, unsigned flags) noexcept {
  if (!dev_ptr) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  CUdeviceptr dptr = 0;
  r = Drv().cuMemHostGetDevicePointer_v2(&dptr, host_ptr, flags);
  if (r == 0) *dev_ptr = reinterpret_cast<void*>(static_cast<uintptr_t>(dptr));
  return r;
}

inline int WrapHipHostFree(void* ptr) noexcept {
  if (!ptr) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuMemFreeHost(ptr);
}

inline int WrapHipMemcpy(void* dst, const void* src, size_t bytes, int kind) noexcept {
  if (bytes == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  switch (kind) {
    case 0: // HostToHost
      std::memcpy(dst, src, bytes);
      return 0;
    case 1: // HostToDevice
      return d.cuMemcpyHtoD_v2(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)), src, bytes);
    case 2: // DeviceToHost
      return d.cuMemcpyDtoH_v2(dst, static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes);
    case 3: // DeviceToDevice
      return d.cuMemcpyDtoD_v2(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                               static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes);
    default:
      return d.cuMemcpy(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                        static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes);
  }
}

inline int WrapHipMemcpyAsync(void* dst, const void* src, size_t bytes, int kind, Handle stream) noexcept {
  if (bytes == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  switch (kind) {
    case 0:
      std::memcpy(dst, src, bytes);
      return 0;
    case 1:
      return d.cuMemcpyHtoDAsync_v2(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)), src, bytes, stream);
    case 2:
      return d.cuMemcpyDtoHAsync_v2(dst, static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes, stream);
    case 3:
      return d.cuMemcpyDtoDAsync_v2(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                                    static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes, stream);
    default:
      return d.cuMemcpyAsync(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                             static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src)), bytes, stream);
  }
}

inline int WrapHipMemcpy2DAsync(void* dst, size_t dpitch, const void* src, size_t spitch,
                                size_t width, size_t height, int kind, Handle stream) noexcept {
  if (width == 0 || height == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  CudaMemcpy2DDesc cp{};
  cp.srcPitch = spitch;
  cp.dstPitch = dpitch;
  cp.WidthInBytes = width;
  cp.Height = height;
  // CUmemorytype: 1 = HOST, 2 = DEVICE, 4 = UNIFIED
  switch (kind) {
    case 0:
      cp.srcMemoryType = 1; cp.srcHost = src;
      cp.dstMemoryType = 1; cp.dstHost = dst;
      break;
    case 1:
      cp.srcMemoryType = 1; cp.srcHost = src;
      cp.dstMemoryType = 2; cp.dstDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst));
      break;
    case 2:
      cp.srcMemoryType = 2; cp.srcDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src));
      cp.dstMemoryType = 1; cp.dstHost = dst;
      break;
    case 3:
      cp.srcMemoryType = 2; cp.srcDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src));
      cp.dstMemoryType = 2; cp.dstDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst));
      break;
    default:
      cp.srcMemoryType = 4; cp.srcDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(src));
      cp.dstMemoryType = 4; cp.dstDevice = static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst));
      break;
  }
  return Drv().cuMemcpy2DAsync_v2(&cp, stream);
}

inline int WrapHipMemsetAsync(void* dst, int value, size_t bytes, Handle stream) noexcept {
  if (bytes == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuMemsetD8Async(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                               static_cast<unsigned char>(value), bytes, stream);
}

inline int WrapHipMemsetD32Async(void* dst, int value, size_t count, Handle stream) noexcept {
  if (count == 0) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuMemsetD32Async(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(dst)),
                                static_cast<unsigned>(value), count, stream);
}

inline int WrapHipEventCreate(Handle* event) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventCreate(event, 0u);
}

inline int WrapHipEventRecord(Handle event, Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventRecord(event, stream);
}

inline int WrapHipEventElapsedTime(float* ms, Handle start, Handle stop) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventElapsedTime(ms, start, stop);
}

inline int WrapHipEventDestroy(Handle event) noexcept {
  if (!event) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventDestroy_v2(event);
}

inline int WrapHipEventSynchronize(Handle event) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventSynchronize(event);
}

inline int WrapHipEventQuery(Handle event) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuEventQuery(event);
}

inline int WrapHipDeviceSynchronize() noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuCtxSynchronize();
}

inline int WrapHipStreamCreate(Handle* stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuStreamCreate(stream, 0u);
}

inline int WrapHipStreamSynchronize(Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuStreamSynchronize(stream);
}

inline int WrapHipStreamDestroy(Handle stream) noexcept {
  if (!stream) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuStreamDestroy_v2(stream);
}

inline int WrapHipStreamQuery(Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuStreamQuery(stream);
}

inline int WrapHipStreamWaitValue32(Handle stream, void* ptr, unsigned value, unsigned flags, unsigned mask) noexcept {
  (void)mask;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (!d.cuStreamWaitValue32_v2) return 801;
  return d.cuStreamWaitValue32_v2(stream, static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)), value, flags);
}

inline int WrapHipImportExternalMemory(Handle* extMem_out, const MemoryDesc* memHandleDesc) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuImportExternalMemory(extMem_out, memHandleDesc);
}

inline int WrapHipExternalMemoryGetMappedBuffer(void** devPtr, Handle extMem, const BufferDesc* bufferDesc) noexcept {
  if (!devPtr) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  CUdeviceptr dptr = 0;
  r = Drv().cuExternalMemoryGetMappedBuffer(&dptr, extMem, bufferDesc);
  if (r == 0) *devPtr = reinterpret_cast<void*>(static_cast<uintptr_t>(dptr));
  return r;
}

inline int WrapHipDestroyExternalMemory(Handle extMem) noexcept {
  if (!extMem) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuDestroyExternalMemory(extMem);
}

inline int WrapHipImportExternalSemaphore(Handle* extSem_out, const SemaphoreDesc* semHandleDesc) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuImportExternalSemaphore(extSem_out, semHandleDesc);
}

inline int WrapHipSignalExternalSemaphoresAsync(const Handle* extSemArray, const SignalParams* paramsArray,
                                                unsigned numExtSems, Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuSignalExternalSemaphoresAsync(extSemArray, paramsArray, numExtSems, stream);
}

inline int WrapHipWaitExternalSemaphoresAsync(const Handle* extSemArray, const WaitParams* paramsArray,
                                              unsigned numExtSems, Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuWaitExternalSemaphoresAsync(extSemArray, paramsArray, numExtSems, stream);
}

inline int WrapHipDestroyExternalSemaphore(Handle extSem) noexcept {
  if (!extSem) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuDestroyExternalSemaphore(extSem);
}

inline int WrapHipStreamBeginCapture(Handle stream, int mode) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuStreamBeginCapture_v2 ? d.cuStreamBeginCapture_v2(stream, mode) : 801;
}

inline int WrapHipStreamEndCapture(Handle stream, Handle* graph) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuStreamEndCapture ? d.cuStreamEndCapture(stream, graph) : 801;
}

inline int WrapHipGraphInstantiate(Handle* graphExec, Handle graph, Handle* errorNode, char* logBuf, size_t bufSize) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (d.cuGraphInstantiateWithFlags) return d.cuGraphInstantiateWithFlags(graphExec, graph, 0ull);
  if (d.cuGraphInstantiate_v2) return d.cuGraphInstantiate_v2(graphExec, graph, errorNode, logBuf, bufSize);
  return 801;
}

inline int WrapHipGraphLaunch(Handle graphExec, Handle stream) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuGraphLaunch ? d.cuGraphLaunch(graphExec, stream) : 801;
}

inline int WrapHipGraphDestroy(Handle graph) noexcept {
  if (!graph) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuGraphDestroy ? d.cuGraphDestroy(graph) : 801;
}

inline int WrapHipGraphExecDestroy(Handle graphExec) noexcept {
  if (!graphExec) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuGraphExecDestroy ? d.cuGraphExecDestroy(graphExec) : 801;
}

inline int WrapHipMemAddressReserve(void** ptr, size_t size, size_t alignment, void* addr, unsigned long long flags) noexcept {
  if (!ptr) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (!d.cuMemAddressReserve) return 801;
  CUdeviceptr dptr = 0;
  r = d.cuMemAddressReserve(&dptr, size, alignment, static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(addr)), flags);
  if (r == 0) *ptr = reinterpret_cast<void*>(static_cast<uintptr_t>(dptr));
  return r;
}

inline int WrapHipMemAddressFree(void* ptr, size_t size) noexcept {
  if (!ptr) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuMemAddressFree ? d.cuMemAddressFree(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)), size) : 801;
}

inline int WrapHipMemCreate(void** handle, size_t size, const MemAllocationProp* prop, unsigned long long flags) noexcept {
  if (!handle || !prop) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (!d.cuMemCreate) return 801;
  MemAllocationProp fixed = *prop;
  if (fixed.location.type == 1 && fixed.location.id == 0) {
    fixed.location.id = d.active_device.load(std::memory_order_relaxed);
  }
  return d.cuMemCreate(handle, size, &fixed, flags);
}

inline int WrapHipMemRelease(void* handle) noexcept {
  if (!handle) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuMemRelease ? d.cuMemRelease(handle) : 801;
}

inline int WrapHipMemMap(void* ptr, size_t size, size_t offset, void* handle, unsigned long long flags) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuMemMap ? d.cuMemMap(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)), size, offset, handle, flags) : 801;
}

inline int WrapHipMemUnmap(void* ptr, size_t size) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuMemUnmap ? d.cuMemUnmap(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)), size) : 801;
}

inline int WrapHipMemSetAccess(void* ptr, size_t size, const MemAccessDesc* desc, size_t count) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  return d.cuMemSetAccess ? d.cuMemSetAccess(static_cast<CUdeviceptr>(reinterpret_cast<uintptr_t>(ptr)), size, desc, count) : 801;
}

inline int WrapHipMemGetAllocationGranularity(size_t* granularity, const MemAllocationProp* prop, unsigned option) noexcept {
  if (!granularity || !prop) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (!d.cuMemGetAllocationGranularity) return 801;
  MemAllocationProp fixed = *prop;
  if (fixed.location.type == 1 && fixed.location.id == 0) {
    fixed.location.id = d.active_device.load(std::memory_order_relaxed);
  }
  return d.cuMemGetAllocationGranularity(granularity, &fixed, static_cast<int>(option));
}

inline int WrapHipModuleLoadData(Handle* module, const void* image) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuModuleLoadData(module, image);
}

inline int WrapHipModuleLoad(Handle* module, const char* fname) noexcept {
  if (!module || !fname) return 1;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto resolved = ResolveModuleFile(fname);
  std::ifstream f(resolved, std::ios::binary | std::ios::ate);
  if (!f) return Drv().cuModuleLoad(module, fname);
  auto n = f.tellg();
  if (n <= 0) return 1;
  std::vector<char> bytes(static_cast<size_t>(n) + 1, 0);
  f.seekg(0);
  if (!f.read(bytes.data(), n)) return 1;
  return Drv().cuModuleLoadData(module, bytes.data());
}

inline int WrapHipModuleGetFunction(Handle* function, Handle module, const char* kname) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  r = d.cuModuleGetFunction(function, module, kname);
  if (r == 0 && function && *function) {
    if (kname) {
      std::lock_guard<std::mutex> lock(d.fn_mutex);
      d.fn_names.emplace_back(*function, kname);
    }
    if (d.cuFuncGetAttribute && d.cuFuncSetAttribute) {
      // Allow > 48 KB shared memory on sm_86 when needed.
      int static_smem = 0;
      if (d.cuFuncGetAttribute(&static_smem, 1 /*CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES*/, *function) == 0 &&
          static_smem > 49152) {
        d.cuFuncSetAttribute(*function, 9 /*CU_FUNC_ATTRIBUTE_PREFERRED_SHARED_MEMORY_CARVEOUT*/, 100);
        d.cuFuncSetAttribute(*function, 8 /*CU_FUNC_ATTRIBUTE_MAX_DYNAMIC_SHARED_SIZE_BYTES*/, 99328 - static_smem);
      }
    }
  }
  return r;
}

inline int WrapHipModuleGetGlobal(void** dptr, size_t* bytes, Handle module, const char* name) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  CUdeviceptr ptr = 0;
  r = Drv().cuModuleGetGlobal_v2(&ptr, bytes, module, name);
  if (r == 0 && dptr) *dptr = reinterpret_cast<void*>(static_cast<uintptr_t>(ptr));
  return r;
}

inline int WrapHipModuleUnload(Handle module) noexcept {
  if (!module) return 0;
  int r = EnsureCurrentContext();
  if (r) return r;
  return Drv().cuModuleUnload(module);
}

inline int WrapHipModuleLaunchKernel(Handle f, unsigned gridX, unsigned gridY, unsigned gridZ,
                                     unsigned blockX, unsigned blockY, unsigned blockZ,
                                     unsigned sharedMemBytes, Handle stream,
                                     void** kernelParams, void** extra) noexcept {
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  if (sharedMemBytes > 49152 && d.cuFuncSetAttribute) {
    d.cuFuncSetAttribute(f, 8 /*CU_FUNC_ATTRIBUTE_MAX_DYNAMIC_SHARED_SIZE_BYTES*/, static_cast<int>(sharedMemBytes));
  }
  r = d.cuLaunchKernel(f, gridX, gridY, gridZ, blockX, blockY, blockZ, sharedMemBytes, stream, kernelParams, extra);
  if (r != 0) {
    int regs = -1, s_smem = -1, max_tpb = -1;
    if (d.cuFuncGetAttribute) {
      d.cuFuncGetAttribute(&max_tpb, 0, f);
      d.cuFuncGetAttribute(&s_smem, 1, f);
      d.cuFuncGetAttribute(&regs, 4, f);
    }
    const char* err_name = nullptr;
    d.cuGetErrorName(r, &err_name);
    std::fprintf(stderr,
                 "[CUDA LAUNCH ERROR] kernel=%s err=%d(%s) grid=(%u,%u,%u) block=(%u,%u,%u) dyn_smem=%u static_smem=%d regs=%d max_tpb=%d\n",
                 d.LookupFnName(f), r, err_name ? err_name : "?",
                 gridX, gridY, gridZ, blockX, blockY, blockZ, sharedMemBytes, s_smem, regs, max_tpb);
  }
  return r;
}

inline int WrapHipExtModuleLaunchKernel(Handle f, unsigned globalX, unsigned globalY, unsigned globalZ,
                                        unsigned localX, unsigned localY, unsigned localZ,
                                        size_t sharedMemBytes, Handle stream,
                                        void** kernelParams, void** extra,
                                        Handle startEvent, Handle stopEvent, unsigned flags) noexcept {
  (void)flags;
  int r = EnsureCurrentContext();
  if (r) return r;
  auto& d = Drv();
  unsigned gridX = localX ? (globalX / localX) : globalX;
  unsigned gridY = localY ? (globalY / localY) : globalY;
  unsigned gridZ = localZ ? (globalZ / localZ) : globalZ;
  if (startEvent) {
    r = d.cuEventRecord(startEvent, stream);
    if (r) return r;
  }
  if (sharedMemBytes > 49152 && d.cuFuncSetAttribute) {
    d.cuFuncSetAttribute(f, 8 /*CU_FUNC_ATTRIBUTE_MAX_DYNAMIC_SHARED_SIZE_BYTES*/, static_cast<int>(sharedMemBytes));
  }
  r = d.cuLaunchKernel(f, gridX, gridY, gridZ, localX, localY, localZ,
                       static_cast<unsigned>(sharedMemBytes), stream, kernelParams, extra);
  if (r == 0 && stopEvent) {
    r = d.cuEventRecord(stopEvent, stream);
  }
  return r;
}

inline const char* WrapHipGetErrorName(int error) noexcept {
  const char* name = nullptr;
  if (Drv().cuGetErrorName(error, &name) == 0 && name) return name;
  return "CUDA_ERROR_UNKNOWN";
}

inline void* LookupCompatSymbol(const char* name) noexcept {
  if (!name) return nullptr;
  struct Entry {
    const char* name;
    void* fn;
  };
  static const Entry kTable[] = {
      {"hipGetDevicePropertiesR0600", reinterpret_cast<void*>(&WrapHipGetDevicePropertiesR0600)},
      {"hipModuleLoadData", reinterpret_cast<void*>(&WrapHipModuleLoadData)},
      {"hipInit", reinterpret_cast<void*>(&WrapHipInit)},
      {"hipRuntimeGetVersion", reinterpret_cast<void*>(&WrapHipRuntimeGetVersion)},
      {"hipGetDeviceCount", reinterpret_cast<void*>(&WrapHipGetDeviceCount)},
      {"hipDeviceGetName", reinterpret_cast<void*>(&WrapHipDeviceGetName)},
      {"hipSetDevice", reinterpret_cast<void*>(&WrapHipSetDevice)},
      {"hipMemGetInfo", reinterpret_cast<void*>(&WrapHipMemGetInfo)},
      {"hipMalloc", reinterpret_cast<void*>(&WrapHipMalloc)},
      {"hipHostMalloc", reinterpret_cast<void*>(&WrapHipHostMalloc)},
      {"hipHostGetDevicePointer", reinterpret_cast<void*>(&WrapHipHostGetDevicePointer)},
      {"hipHostFree", reinterpret_cast<void*>(&WrapHipHostFree)},
      {"hipFree", reinterpret_cast<void*>(&WrapHipFree)},
      {"hipMemcpy", reinterpret_cast<void*>(&WrapHipMemcpy)},
      {"hipMemcpyAsync", reinterpret_cast<void*>(&WrapHipMemcpyAsync)},
      {"hipMemcpy2DAsync", reinterpret_cast<void*>(&WrapHipMemcpy2DAsync)},
      {"hipMemsetAsync", reinterpret_cast<void*>(&WrapHipMemsetAsync)},
      {"hipMemsetD32Async", reinterpret_cast<void*>(&WrapHipMemsetD32Async)},
      {"hipEventCreate", reinterpret_cast<void*>(&WrapHipEventCreate)},
      {"hipEventRecord", reinterpret_cast<void*>(&WrapHipEventRecord)},
      {"hipEventElapsedTime", reinterpret_cast<void*>(&WrapHipEventElapsedTime)},
      {"hipEventDestroy", reinterpret_cast<void*>(&WrapHipEventDestroy)},
      {"hipEventSynchronize", reinterpret_cast<void*>(&WrapHipEventSynchronize)},
      {"hipEventQuery", reinterpret_cast<void*>(&WrapHipEventQuery)},
      {"hipDeviceSynchronize", reinterpret_cast<void*>(&WrapHipDeviceSynchronize)},
      {"hipStreamCreate", reinterpret_cast<void*>(&WrapHipStreamCreate)},
      {"hipStreamSynchronize", reinterpret_cast<void*>(&WrapHipStreamSynchronize)},
      {"hipStreamDestroy", reinterpret_cast<void*>(&WrapHipStreamDestroy)},
      {"hipStreamQuery", reinterpret_cast<void*>(&WrapHipStreamQuery)},
      {"hipStreamWaitValue32", reinterpret_cast<void*>(&WrapHipStreamWaitValue32)},
      {"hipImportExternalMemory", reinterpret_cast<void*>(&WrapHipImportExternalMemory)},
      {"hipExternalMemoryGetMappedBuffer", reinterpret_cast<void*>(&WrapHipExternalMemoryGetMappedBuffer)},
      {"hipDestroyExternalMemory", reinterpret_cast<void*>(&WrapHipDestroyExternalMemory)},
      {"hipImportExternalSemaphore", reinterpret_cast<void*>(&WrapHipImportExternalSemaphore)},
      {"hipSignalExternalSemaphoresAsync", reinterpret_cast<void*>(&WrapHipSignalExternalSemaphoresAsync)},
      {"hipWaitExternalSemaphoresAsync", reinterpret_cast<void*>(&WrapHipWaitExternalSemaphoresAsync)},
      {"hipDestroyExternalSemaphore", reinterpret_cast<void*>(&WrapHipDestroyExternalSemaphore)},
      {"hipStreamBeginCapture", reinterpret_cast<void*>(&WrapHipStreamBeginCapture)},
      {"hipStreamEndCapture", reinterpret_cast<void*>(&WrapHipStreamEndCapture)},
      {"hipGraphInstantiate", reinterpret_cast<void*>(&WrapHipGraphInstantiate)},
      {"hipGraphLaunch", reinterpret_cast<void*>(&WrapHipGraphLaunch)},
      {"hipGraphDestroy", reinterpret_cast<void*>(&WrapHipGraphDestroy)},
      {"hipGraphExecDestroy", reinterpret_cast<void*>(&WrapHipGraphExecDestroy)},
      {"hipMemAddressReserve", reinterpret_cast<void*>(&WrapHipMemAddressReserve)},
      {"hipMemAddressFree", reinterpret_cast<void*>(&WrapHipMemAddressFree)},
      {"hipMemCreate", reinterpret_cast<void*>(&WrapHipMemCreate)},
      {"hipMemRelease", reinterpret_cast<void*>(&WrapHipMemRelease)},
      {"hipMemMap", reinterpret_cast<void*>(&WrapHipMemMap)},
      {"hipMemUnmap", reinterpret_cast<void*>(&WrapHipMemUnmap)},
      {"hipMemSetAccess", reinterpret_cast<void*>(&WrapHipMemSetAccess)},
      {"hipMemGetAllocationGranularity", reinterpret_cast<void*>(&WrapHipMemGetAllocationGranularity)},
      {"hipModuleLoad", reinterpret_cast<void*>(&WrapHipModuleLoad)},
      {"hipModuleGetFunction", reinterpret_cast<void*>(&WrapHipModuleGetFunction)},
      {"hipModuleGetGlobal", reinterpret_cast<void*>(&WrapHipModuleGetGlobal)},
      {"hipModuleLaunchKernel", reinterpret_cast<void*>(&WrapHipModuleLaunchKernel)},
      {"hipExtModuleLaunchKernel", reinterpret_cast<void*>(&WrapHipExtModuleLaunchKernel)},
      {"hipModuleUnload", reinterpret_cast<void*>(&WrapHipModuleUnload)},
      {"hipGetErrorName", reinterpret_cast<void*>(&WrapHipGetErrorName)},
  };
  for (const auto& e : kTable) {
    if (std::strcmp(e.name, name) == 0) return e.fn;
  }
  return RawSym(Drv().dll, name);
}
} // namespace detail

struct Api {
  HMODULE dll{};
#define HIP_FN(name, args) \
  using name##Fn = int(*) args; \
  name##Fn name {}
  HIP_FN(hipGetDevicePropertiesR0600, (DevicePropertiesR0600*, int));
  HIP_FN(hipModuleLoadData, (Handle*, const void*));
  HIP_FN(hipInit, (unsigned));
  HIP_FN(hipRuntimeGetVersion, (int*));
  HIP_FN(hipGetDeviceCount, (int*));
  HIP_FN(hipDeviceGetName, (char*, int, int));
  HIP_FN(hipSetDevice, (int));
  HIP_FN(hipMemGetInfo, (size_t*, size_t*));
  HIP_FN(hipMalloc, (void**, size_t));
  HIP_FN(hipHostMalloc, (void**, size_t, unsigned));
  HIP_FN(hipHostGetDevicePointer, (void**, void*, unsigned));
  HIP_FN(hipHostFree, (void*));
  HIP_FN(hipFree, (void*));
  HIP_FN(hipMemcpy, (void*, const void*, size_t, int));
  HIP_FN(hipMemcpyAsync, (void*, const void*, size_t, int, Handle));
  HIP_FN(hipMemcpy2DAsync, (void*, size_t, const void*, size_t, size_t, size_t, int, Handle));
  HIP_FN(hipMemsetAsync, (void*, int, size_t, Handle));
  HIP_FN(hipMemsetD32Async, (void*, int, size_t, Handle));
  HIP_FN(hipEventCreate, (Handle*));
  HIP_FN(hipEventRecord, (Handle, Handle));
  HIP_FN(hipEventElapsedTime, (float*, Handle, Handle));
  HIP_FN(hipEventDestroy, (Handle));
  HIP_FN(hipEventSynchronize, (Handle));
  HIP_FN(hipEventQuery, (Handle));
  HIP_FN(hipDeviceSynchronize, ());
  HIP_FN(hipStreamCreate, (Handle*));
  HIP_FN(hipStreamSynchronize, (Handle));
  HIP_FN(hipStreamDestroy, (Handle));
  HIP_FN(hipStreamQuery, (Handle));
  HIP_FN(hipStreamWaitValue32, (Handle, void*, unsigned, unsigned, unsigned));
  HIP_FN(hipImportExternalMemory, (Handle*, const MemoryDesc*));
  HIP_FN(hipExternalMemoryGetMappedBuffer, (void**, Handle, const BufferDesc*));
  HIP_FN(hipDestroyExternalMemory, (Handle));
  HIP_FN(hipImportExternalSemaphore, (Handle*, const SemaphoreDesc*));
  HIP_FN(hipSignalExternalSemaphoresAsync, (const Handle*, const SignalParams*, unsigned, Handle));
  HIP_FN(hipWaitExternalSemaphoresAsync, (const Handle*, const WaitParams*, unsigned, Handle));
  HIP_FN(hipDestroyExternalSemaphore, (Handle));
  // Optional graph API, loaded only when requested.
  HIP_FN(hipStreamBeginCapture, (Handle, int));
  HIP_FN(hipStreamEndCapture, (Handle, Handle*));
  HIP_FN(hipGraphInstantiate, (Handle*, Handle, Handle*, char*, size_t));
  HIP_FN(hipGraphLaunch, (Handle, Handle));
  HIP_FN(hipGraphDestroy, (Handle));
  HIP_FN(hipGraphExecDestroy, (Handle));
  // Optional VMM API (EnableVmm): address reservation + physical chunks mapped at chosen offsets.
  HIP_FN(hipMemAddressReserve, (void**, size_t, size_t, void*, unsigned long long));
  HIP_FN(hipMemAddressFree, (void*, size_t));
  HIP_FN(hipMemCreate, (void**, size_t, const MemAllocationProp*, unsigned long long));
  HIP_FN(hipMemRelease, (void*));
  HIP_FN(hipMemMap, (void*, size_t, size_t, void*, unsigned long long));
  HIP_FN(hipMemUnmap, (void*, size_t));
  HIP_FN(hipMemSetAccess, (void*, size_t, const MemAccessDesc*, size_t));
  HIP_FN(hipMemGetAllocationGranularity, (size_t*, const MemAllocationProp*, unsigned));
  HIP_FN(hipModuleLoad, (Handle*, const char*));
  HIP_FN(hipModuleGetFunction, (Handle*, Handle, const char*));
  HIP_FN(hipModuleLaunchKernel, (Handle, unsigned, unsigned, unsigned, unsigned, unsigned, unsigned, unsigned, Handle, void**, void**));
  HIP_FN(hipExtModuleLaunchKernel, (Handle, unsigned, unsigned, unsigned, unsigned, unsigned, unsigned, size_t, Handle, void**, void**, Handle, Handle, unsigned));
  HIP_FN(hipModuleUnload, (Handle));
#undef HIP_FN
  using ErrorNameFn = const char* (*)(int);
  ErrorNameFn hipGetErrorName{};

  void* GetSymbol(const char* n) const noexcept {
    return detail::LookupCompatSymbol(n);
  }

  template <class T>
  void Load(T& f, const char* n) {
    f = reinterpret_cast<T>(detail::LookupCompatSymbol(n));
    if (!f) throw std::runtime_error(std::string("missing CUDA/HIP export ") + n);
  }

  explicit Api(unsigned version = 7) {
    (void)version;
    dll = detail::Drv().dll;
#define LOAD(name) Load(name, #name)
    LOAD(hipGetDevicePropertiesR0600);
    LOAD(hipModuleLoadData);
    LOAD(hipEventCreate);
    LOAD(hipEventRecord);
    LOAD(hipEventElapsedTime);
    LOAD(hipEventDestroy);
    LOAD(hipEventSynchronize);
    LOAD(hipEventQuery);
    LOAD(hipHostMalloc);
    LOAD(hipHostGetDevicePointer);
    LOAD(hipHostFree);
    LOAD(hipInit);
    LOAD(hipRuntimeGetVersion);
    LOAD(hipGetDeviceCount);
    LOAD(hipDeviceGetName);
    LOAD(hipSetDevice);
    LOAD(hipMemGetInfo);
    LOAD(hipMalloc);
    LOAD(hipFree);
    LOAD(hipMemcpy);
    LOAD(hipMemcpyAsync);
    LOAD(hipMemcpy2DAsync);
    LOAD(hipMemsetAsync);
    LOAD(hipMemsetD32Async);
    LOAD(hipDeviceSynchronize);
    LOAD(hipStreamCreate);
    LOAD(hipStreamSynchronize);
    LOAD(hipStreamDestroy);
    LOAD(hipStreamQuery);
    LOAD(hipStreamWaitValue32);
    LOAD(hipImportExternalMemory);
    LOAD(hipExternalMemoryGetMappedBuffer);
    LOAD(hipDestroyExternalMemory);
    LOAD(hipImportExternalSemaphore);
    LOAD(hipSignalExternalSemaphoresAsync);
    LOAD(hipWaitExternalSemaphoresAsync);
    LOAD(hipDestroyExternalSemaphore);
    LOAD(hipModuleLoad);
    LOAD(hipModuleGetFunction);
    LOAD(hipModuleGetGlobal);
    LOAD(hipModuleLaunchKernel);
    LOAD(hipExtModuleLaunchKernel);
    LOAD(hipModuleUnload);
    LOAD(hipGetErrorName);
#undef LOAD
  }

  DevicePropertiesR0600 Properties(int device) {
    DevicePropertiesR0600 p{};
    Check(hipGetDevicePropertiesR0600(&p, device), "device properties");
    return p;
  }

  /* DLSS5_STYLE (2026-10-01): when >=0, every module that defines the device constant `dlss5_style_feature` (preprocess feature 6,
     Style/128; modules default to 1/128) gets this value right after loading. -1 = leave the module default (no extra HIP calls). */
  float style_feature = -1;
  using ModuleGetGlobalFn = int (*)(void**, size_t*, Handle, const char*);
  ModuleGetGlobalFn hipModuleGetGlobal{};

  int LoadModule(Handle* module, const char* path) {
    auto resolved = detail::ResolveModuleFile(path);
    std::ifstream f(resolved, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error(std::string("module file missing: ") + path);
    auto n = f.tellg();
    if (n <= 0) throw std::runtime_error("empty module");
    // Null-terminate buffer so both binary (.cubin/.fatbin) and PTX text files work with cuModuleLoadData.
    std::vector<char> bytes(static_cast<size_t>(n) + 1, 0);
    f.seekg(0);
    if (!f.read(bytes.data(), n)) throw std::runtime_error("module read failed");
    // Publish ownership only after optional module initialization succeeds.
    *module = nullptr;
    Handle loaded = nullptr;
    int r = hipModuleLoadData(&loaded, bytes.data());
    if (r) return r;
    try {
      if (style_feature >= 0) {
        if (!hipModuleGetGlobal) Load(hipModuleGetGlobal, "hipModuleGetGlobal");
        void* p = nullptr;
        size_t s = 0;
        if (!hipModuleGetGlobal(&p, &s, loaded, "dlss5_style_feature") && p && s == sizeof(float))
          Check(hipMemcpy(p, &style_feature, sizeof(float), 1), "DLSS5_STYLE");
      }
    } catch (...) {
      hipModuleUnload(loaded);
      throw;
    }
    *module = loaded;
    return 0;
  }

  void EnableVmm() {
    Load(hipMemAddressReserve, "hipMemAddressReserve");
    Load(hipMemAddressFree, "hipMemAddressFree");
    Load(hipMemCreate, "hipMemCreate");
    Load(hipMemRelease, "hipMemRelease");
    Load(hipMemMap, "hipMemMap");
    Load(hipMemUnmap, "hipMemUnmap");
    Load(hipMemSetAccess, "hipMemSetAccess");
    Load(hipMemGetAllocationGranularity, "hipMemGetAllocationGranularity");
  }

  void EnableGraphs() {
    Load(hipStreamBeginCapture, "hipStreamBeginCapture");
    Load(hipStreamEndCapture, "hipStreamEndCapture");
    Load(hipGraphInstantiate, "hipGraphInstantiate");
    Load(hipGraphLaunch, "hipGraphLaunch");
    Load(hipGraphDestroy, "hipGraphDestroy");
    Load(hipGraphExecDestroy, "hipGraphExecDestroy");
  }

  void Check(int result, const char* what) {
    if (result)
      throw std::runtime_error(std::string(what) + ": " + hipGetErrorName(result) + " (" + std::to_string(result) + ")");
  }
  // Keep runtime loaded until process teardown: driver-owned workers may outlive probe objects.
};
} // namespace hip_probe

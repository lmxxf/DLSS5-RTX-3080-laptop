// Device-only gfx1201 module. No host runtime, BLAS, scalar GEMM or fallback.
// ABI and validation: wmma_probe.md. Keep input FP8 BYTES identical to HLSL.
#define __device__ __attribute__((device))
#define __global__ __attribute__((global))
#define __forceinline__ __attribute__((always_inline)) inline
#define __launch_bounds__(n) __attribute__((amdgpu_flat_work_group_size(n,n)))

#if defined(__HIP_DEVICE_COMPILE__)
#if !defined(__gfx1201__)
#error "WMMA probe is deliberately restricted to gfx1201"
#endif
#if !__has_builtin(__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12)
#error "Compiler lacks gfx12 FP8 WMMA; no scalar fallback permitted"
#endif
#if !__has_builtin(__builtin_amdgcn_cvt_pk_fp8_f32)
#error "Compiler lacks native FP8 conversion"
#endif
#endif

using i2 = int __attribute__((ext_vector_type(2)));
using f8 = float __attribute__((ext_vector_type(8)));
using h8 = _Float16 __attribute__((ext_vector_type(8)));
using u8 = unsigned char;
using u16 = unsigned short;
using u32 = unsigned int;
static_assert(sizeof(i2)==8 && sizeof(f8)==32 && sizeof(h8)==16, "fragment ABI");

// gfx12 wave32: no RDNA3 duplication. Each lane owns eight K entries.
// Mathematical row-major ABI: A[16][32], B[32][16], C/D[16][16].
// A fragment: row=lane%16, K=(lane/16)*8+element (+tile*16).
// B fragment: K=same, column=lane%16. C/D row=group*8+element,col=lane%16.
__device__ __forceinline__ float unpack_fp8(u8 bits) {
    return __builtin_amdgcn_cvt_f32_fp8(int(bits), 0);
}

template<bool UseFP8>
__device__ __forceinline__ void run_tile(const u8* a, const u8* b, const float* c,
    float* d, float* after_k16, u16* d_half_rne, u32* status, u32 count) {
    const u32 batch=__builtin_amdgcn_workgroup_id_x();
    if(batch>=count)return;
    // The dynamic host enforces grid(count,1,1), block(32,1,1).
    const u32 lane=__builtin_amdgcn_workitem_id_x(), rc=lane&15, group=lane>>4;
    a+=batch*512; b+=batch*512; c+=batch*256;
    d+=batch*256; after_k16+=batch*256; d_half_rne+=batch*256;
    f8 acc{};
#pragma unroll
    for(u32 e=0;e<8;++e)acc[e]=c[(group*8+e)*16+rc];
#pragma unroll
    for(u32 tile=0;tile<2;++tile) {
        i2 pa{},pb{}; h8 ha{},hb{};
#pragma unroll
        for(u32 e=0;e<8;++e) {
            const u32 k=tile*16+group*8+e;
            const u8 av=a[rc*32+k], bv=b[k*16+rc];
            if constexpr(UseFP8) {
                // Each little-endian int packs four FP8 values in K order.
                pa[e/4]=int(u32(pa[e/4]) | (u32(av)<<(8*(e%4))));
                pb[e/4]=int(u32(pb[e/4]) | (u32(bv)<<(8*(e%4))));
            } else {
                // Every finite E4M3 value is exactly representable in F16.
                // This is a separately named matrix-core reference, NEVER a
                // replacement implementation of the FP8 entry point.
                ha[e]=(_Float16)unpack_fp8(av);
                hb[e]=(_Float16)unpack_fp8(bv);
            }
        }
        if constexpr(UseFP8)
            acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(pa,pb,acc);
        else
            acc=__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(ha,hb,acc);
        if(tile==0) {
#pragma unroll
            for(u32 e=0;e<8;++e)after_k16[(group*8+e)*16+rc]=acc[e];
        }
    }
#pragma unroll
    for(u32 e=0;e<8;++e) {
        const u32 offset=(group*8+e)*16+rc;
        d[offset]=acc[e];
        d_half_rne[offset]=__builtin_bit_cast(u16, (_Float16)acc[e]);
    }
    if(lane==0)status[batch]=0;
}

// hipModuleGetFunction by unmangled name; launch grid=(count,1,1),block=(32,1,1).
// Pointer arguments are device addresses, final count is a 32-bit scalar.
extern "C" __global__ __launch_bounds__(32)
void dlss5_wmma_fp8_k32(const u8* a,const u8* b,const float* c,float* d,
    float* after_k16,u16* d_half_rne,u32* status,u32 count) {
    run_tile<true>(a,b,c,d,after_k16,d_half_rne,status,count);
}
extern "C" __global__ __launch_bounds__(32)
void dlss5_wmma_f16_k32(const u8* a,const u8* b,const float* c,float* d,
    float* after_k16,u16* d_half_rne,u32* status,u32 count) {
    run_tile<false>(a,b,c,d,after_k16,d_half_rne,status,count);
}

// Conversion is measured separately from GEMM. finite_sat follows AMD's
// cast_to_f8_from_f32 scalar fast path: finite inputs clip to +/-448, NaN/Inf
// pass to hardware. Also return unclamped bytes to expose saturation behavior.
// Launch 1D blocks of exactly64 lanes; output arrays each contain count bytes.
extern "C" __global__ void dlss5_fp8_convert(const float* input,u8* raw,
    u8* finite_sat,float* decoded,u32 count) {
    const u32 i=__builtin_amdgcn_workgroup_id_x()*64u+__builtin_amdgcn_workitem_id_x();
    if(i>=count)return;
    const float v=input[i];
    raw[i]=u8(__builtin_amdgcn_cvt_pk_fp8_f32(v,v,0,false));
    const u32 bits=__builtin_bit_cast(u32,v);
    const float clipped=(bits&0x7f800000u)==0x7f800000u?v:
        __builtin_amdgcn_fmed3f(v,448.0f,-448.0f);
    const u8 q=u8(__builtin_amdgcn_cvt_pk_fp8_f32(clipped,clipped,0,false));
    finite_sat[i]=q; decoded[i]=unpack_fp8(q);
}

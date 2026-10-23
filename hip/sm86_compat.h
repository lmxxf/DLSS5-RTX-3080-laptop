#pragma once

// ============================================================================
// sm86_compat.h — RDNA4 Wave32 (gfx1201) -> NVIDIA Ampere (sm_86) Device Layer
// Compiles SDK-free HIP kernels with:
//   clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -nocudainc -nocudalib -std=c++20 -O3
// ============================================================================

#define _Float16 __fp16
#define amdgpu_flat_work_group_size(lo, hi) launch_bounds(hi)
#define amdgpu_waves_per_eu(...)

#ifndef __HIP_MEMORY_SCOPE_AGENT
#define __HIP_MEMORY_SCOPE_AGENT 1
#endif
#ifndef __HIP_MEMORY_SCOPE_SYSTEM
#define __HIP_MEMORY_SCOPE_SYSTEM 2
#endif

#define SM86_DEV __attribute__((device)) __attribute__((always_inline)) inline

typedef unsigned char sm86_u8;
typedef unsigned short sm86_u16;
typedef unsigned int sm86_u32;
typedef unsigned long long sm86_u64;
typedef unsigned long size_t;
typedef int sm86_i2 __attribute__((ext_vector_type(2)));
typedef int sm86_i4 __attribute__((ext_vector_type(4)));
typedef sm86_u32 sm86_u4 __attribute__((ext_vector_type(4)));
typedef float sm86_f8 __attribute__((ext_vector_type(8)));
typedef _Float16 sm86_h2 __attribute__((ext_vector_type(2)));
typedef _Float16 sm86_h8 __attribute__((ext_vector_type(8)));

// --- Thread & Block Indexing ---
SM86_DEV sm86_u32 __builtin_amdgcn_workitem_id_x() {
    return __nvvm_read_ptx_sreg_tid_x();
}

SM86_DEV sm86_u32 __builtin_amdgcn_workgroup_id_x() {
    return __nvvm_read_ptx_sreg_ctaid_x();
}

SM86_DEV sm86_u32 sm86_lane_id() {
    sm86_u32 r;
    asm("mov.u32 %0, %%laneid;" : "=r"(r));
    return r;
}

// --- Synchronization, Barriers & Fences ---
SM86_DEV void __builtin_amdgcn_s_barrier() {
    asm volatile("bar.sync 0;" ::: "memory");
}

SM86_DEV void __builtin_amdgcn_wave_barrier() {
    asm volatile("bar.warp.sync 0xffffffff;" ::: "memory");
}

SM86_DEV void __builtin_amdgcn_fence(sm86_u32 /*order*/, const char* scope, const char* /*s2*/ = "") {
    if (scope && scope[0] == 'a') {
        asm volatile("membar.gl;" ::: "memory");
    } else {
        asm volatile("" ::: "memory");
    }
}

SM86_DEV void __builtin_amdgcn_sched_barrier(int) {
    asm volatile("" ::: "memory");
}

SM86_DEV void __builtin_amdgcn_s_sleep(int) {
    asm volatile("nanosleep.u32 64;");
}

SM86_DEV void __builtin_amdgcn_s_setreg(int, int) {}

SM86_DEV sm86_u64 sm86_readsteadycounter() {
    sm86_u64 r;
    asm volatile("mov.u64 %0, %%clock64;" : "=l"(r));
    return r;
}
#define __builtin_readsteadycounter() sm86_readsteadycounter()

template <typename T>
SM86_DEV void sm86_keep_alive(T& v) {
    if constexpr (__is_floating_point(T)) {
        asm volatile("" : "+f"(v));
    } else {
        asm volatile("" : "+r"(v));
    }
}

// --- Atomics for swin_persistent ---
SM86_DEV sm86_u32 sm86_hip_atomic_load(const sm86_u32* p, int order, int /*scope*/) {
    sm86_u32 r;
    asm volatile("ld.global.cg.u32 %0, [%1];" : "=r"(r) : "l"(p) : "memory");
    if (order == __ATOMIC_ACQUIRE || order == __ATOMIC_ACQ_REL || order == __ATOMIC_SEQ_CST) {
        asm volatile("membar.gl;" ::: "memory");
    }
    return r;
}
#define __hip_atomic_load sm86_hip_atomic_load

SM86_DEV void sm86_hip_atomic_store(sm86_u32* p, sm86_u32 val, int order, int /*scope*/) {
    if (order == __ATOMIC_RELEASE || order == __ATOMIC_ACQ_REL || order == __ATOMIC_SEQ_CST) {
        asm volatile("membar.gl;" ::: "memory");
    }
    asm volatile("st.global.wb.u32 [%0], %1;" :: "l"(p), "r"(val) : "memory");
}
#define __hip_atomic_store sm86_hip_atomic_store

SM86_DEV sm86_u32 sm86_hip_atomic_exchange(sm86_u32* p, sm86_u32 val, int /*order*/, int /*scope*/) {
    sm86_u32 r;
    asm volatile("atom.global.exch.b32 %0, [%1], %2;" : "=r"(r) : "l"(p), "r"(val) : "memory");
    return r;
}
#define __hip_atomic_exchange sm86_hip_atomic_exchange

SM86_DEV sm86_u32 sm86_hip_atomic_fetch_add(sm86_u32* p, sm86_u32 val, int /*order*/, int /*scope*/) {
    sm86_u32 r;
    asm volatile("atom.global.add.u32 %0, [%1], %2;" : "=r"(r) : "l"(p), "r"(val) : "memory");
    return r;
}
#define __hip_atomic_fetch_add sm86_hip_atomic_fetch_add

// --- Warp Shuffle & Lane Intrinsics ---
SM86_DEV sm86_u32 sm86_shfl_idx_u32(sm86_u32 val, sm86_u32 src_lane) {
    sm86_u32 r;
    asm("shfl.sync.idx.b32 %0, %1, %2, 0x1f, 0xffffffff;" : "=r"(r) : "r"(val), "r"(src_lane));
    return r;
}

SM86_DEV sm86_u32 sm86_shfl_xor_u32(sm86_u32 val, sm86_u32 mask) {
    sm86_u32 r;
    asm("shfl.sync.bfly.b32 %0, %1, %2, 0x1f, 0xffffffff;" : "=r"(r) : "r"(val), "r"(mask));
    return r;
}

SM86_DEV float sm86_shfl_idx_f32(float val, sm86_u32 src_lane) {
    float r;
    asm("shfl.sync.idx.b32 %0, %1, %2, 0x1f, 0xffffffff;" : "=f"(r) : "f"(val), "r"(src_lane));
    return r;
}

SM86_DEV float sm86_shfl_xor_f32(float val, sm86_u32 mask) {
    float r;
    asm("shfl.sync.bfly.b32 %0, %1, %2, 0x1f, 0xffffffff;" : "=f"(r) : "f"(val), "r"(mask));
    return r;
}

SM86_DEV int __builtin_amdgcn_readfirstlane(int x) {
    return (int)sm86_shfl_idx_u32((sm86_u32)x, 0u);
}

SM86_DEV int __builtin_amdgcn_readlane(int x, int lane) {
    return (int)sm86_shfl_idx_u32((sm86_u32)x, (sm86_u32)lane);
}

SM86_DEV int __builtin_amdgcn_ds_bpermute(int addr_bytes, int val) {
    return (int)sm86_shfl_idx_u32((sm86_u32)val, ((sm86_u32)addr_bytes) >> 2);
}

// --- Math Intrinsics (AMDGPU hardware semantics) ---
SM86_DEV float __builtin_amdgcn_rcpf(float x) {
    float r;
    asm("rcp.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(x));
    return r;
}

SM86_DEV float __builtin_amdgcn_rsqf(float x) {
    float r;
    asm("rsqrt.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(x));
    return r;
}

SM86_DEV float __builtin_amdgcn_sqrtf(float x) {
    float r;
    asm("sqrt.rn.f32 %0, %1;" : "=f"(r) : "f"(x));
    return r;
}

// AMDGPU v_log_f32 is base-2 log2(x)
SM86_DEV float __builtin_amdgcn_logf(float x) {
    float r;
    asm("lg2.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(x));
    return r;
}

// AMDGPU v_sin_f32 / v_cos_f32 take turns (radians / 2pi), so multiply by 2pi
SM86_DEV float __builtin_amdgcn_sinf(float x) {
    float r, rad = x * 6.28318530717958647692f;
    asm("sin.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(rad));
    return r;
}

SM86_DEV float __builtin_amdgcn_cosf(float x) {
    float r, rad = x * 6.28318530717958647692f;
    asm("cos.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(rad));
    return r;
}

// AMDGPU v_med3_f32: median of 3 floats; if x is NaN and (y,z) are finite bounds, returns min(y,z) (-448.f)
SM86_DEV float __builtin_amdgcn_fmed3f(float a, float b, float c) {
    float lo, hi, t, r;
    asm("min.f32 %0, %2, %3;\n\t"
        "max.f32 %1, %2, %3;\n\t"
        "max.f32 %0, %4, %0;\n\t"
        "min.f32 %0, %0, %1;"
        : "=&f"(r), "=&f"(hi)
        : "f"(b), "f"(c), "f"(a));
    return r;
}

// --- FP16 Conversion Helpers (for inline ASM & cvt_pkrtz) ---
SM86_DEV sm86_u32 sm86_v_cvt_f16_f32(float x) {
    sm86_u32 r;
    asm("{ .reg .b16 h;\n\t"
        "  cvt.rn.f16.f32 h, %1;\n\t"
        "  cvt.u32.u16 %0, h; }"
        : "=r"(r) : "f"(x));
    return r;
}

SM86_DEV float sm86_v_cvt_f32_f16(sm86_u32 h) {
    float r;
    asm("{ .reg .b16 lo, hi;\n\t"
        "  mov.b32 {lo, hi}, %1;\n\t"
        "  cvt.f32.f16 %0, lo; }"
        : "=f"(r) : "r"(h));
    return r;
}

SM86_DEV sm86_u32 sm86_v_cvt_pkrtz_f16_f32(float a, float b) {
    sm86_u32 r;
    asm("{ .reg .b16 lo, hi;\n\t"
        "  cvt.rz.f16.f32 lo, %1;\n\t"
        "  cvt.rz.f16.f32 hi, %2;\n\t"
        "  mov.b32 %0, {lo, hi}; }"
        : "=r"(r) : "f"(a), "f"(b));
    return r;
}

SM86_DEV sm86_h2 __builtin_amdgcn_cvt_pkrtz(float a, float b) {
    return __builtin_bit_cast(sm86_h2, sm86_v_cvt_pkrtz_f16_f32(a, b));
}

// --- OCP E4M3 (FP8, bias 7, max 448) <-> FP16 / FP32 ---
// Branchless single-cycle PRMT exact conversion of any E4M3 byte (0..255) to IEEE FP16 bit pattern
SM86_DEV sm86_u16 sm86_e4m3_to_f16_bits(sm86_u32 b) {
    sm86_u32 s = (b & 0x80u) << 8;
    sm86_u32 a = b & 0x7fu;
    sm86_u32 sub;
    asm("prmt.b32 %0, 0x1e1c1800, 0x23222120, %1;" : "=r"(sub) : "r"(a));
    sm86_u32 norm = (a == 0x7fu) ? 0x7e00u : ((a << 7) + 0x2000u);
    sm86_u32 mag = (a < 8u) ? ((sub & 0xffu) << 8) : norm;
    return (sm86_u16)(s | mag);
}

SM86_DEV float __builtin_amdgcn_cvt_f32_fp8(int src, int byte_sel) {
    sm86_u32 b = (((sm86_u32)src) >> (8 * (byte_sel & 3))) & 0xffu;
    return sm86_v_cvt_f32_f16((sm86_u32)sm86_e4m3_to_f16_bits(b));
}

// Exact RNE conversion of FP32 to OCP E4M3 byte (saturating finite >448 to +-448 = 0x7e, Inf/NaN to 0x7f)
SM86_DEV sm86_u32 sm86_f32_to_e4m3_byte(float x) {
    sm86_u32 b = __builtin_bit_cast(sm86_u32, x);
    sm86_u32 s = (b >> 24) & 0x80u;
    sm86_u32 a = b & 0x7fffffffu;
    if (a >= 0x7f800000u) {
        return s | 0x7fu;
    }
    if (a < 0x3c800000u) {
        // Subnormal E4M3: RNE to 2^-9 grid via IEEE f32 add with 16384.0f (0x46800000, ULP = 2^-9)
        float magic;
        asm("add.rn.f32 %0, %1, 0f46800000;" : "=f"(magic) : "f"(__builtin_bit_cast(float, a)));
        return s | (__builtin_bit_cast(sm86_u32, magic) & 0xffu);
    }
    sm86_u32 r = a + 0x7ffffu + ((a >> 20) & 1u);
    if (r >= 0x43e00000u) {
        return s | 0x7eu;
    }
    return s | ((r >> 20) - 0x3c0u);
}

SM86_DEV int __builtin_amdgcn_cvt_pk_fp8_f32(float a, float b, int old, bool word_sel) {
    sm86_u32 lo = sm86_f32_to_e4m3_byte(a);
    sm86_u32 hi = sm86_f32_to_e4m3_byte(b);
    sm86_u32 pair16 = lo | (hi << 8);
    sm86_u32 uold = (sm86_u32)old;
    return (int)(word_sel ? ((uold & 0x0000ffffu) | (pair16 << 16))
                          : ((uold & 0xffff0000u) | pair16));
}

// --- RDNA4 Wave32 16x16x16 WMMA -> Ampere m16n8k16 Tensor Core ---
SM86_DEV void sm86_frag_butterfly(sm86_u4 u, sm86_u32 &r0, sm86_u32 &r1, sm86_u32 &r2, sm86_u32 &r3, sm86_u32 lane) {
    sm86_u32 v0 = u[0], v1 = u[1], v2 = u[2], v3 = u[3];
    bool b0 = (lane & 8u) != 0;
    sm86_u32 s0 = sm86_shfl_xor_u32(b0 ? v0 : v1, 8u);
    sm86_u32 s1 = sm86_shfl_xor_u32(b0 ? v2 : v3, 8u);
    v0 = b0 ? s0 : v0;
    v1 = b0 ? v1 : s0;
    v2 = b0 ? s1 : v2;
    v3 = b0 ? v3 : s1;

    bool b1 = (lane & 16u) != 0;
    sm86_u32 s2 = sm86_shfl_xor_u32(b1 ? v0 : v2, 16u);
    sm86_u32 s3 = sm86_shfl_xor_u32(b1 ? v1 : v3, 16u);
    v0 = b1 ? s2 : v0;
    v2 = b1 ? v2 : s2;
    v1 = b1 ? s3 : v1;
    v3 = b1 ? v3 : s3;

    sm86_u32 src = ((lane & 3u) << 3) | (lane >> 2);
    r0 = sm86_shfl_idx_u32(v0, src);
    r1 = sm86_shfl_idx_u32(v1, src);
    r2 = sm86_shfl_idx_u32(v2, src);
    r3 = sm86_shfl_idx_u32(v3, src);
}

SM86_DEV void sm86_rdna4_c_to_ampere(sm86_f8 c, float &d0, float &d1, float &d2, float &d3,
                                     float &d4, float &d5, float &d6, float &d7, sm86_u32 lane) {
    sm86_u32 src = (lane & 24u) | ((lane & 3u) << 1) | ((lane >> 2) & 1u);
    d0 = sm86_shfl_idx_f32(c[0], src);
    d1 = sm86_shfl_idx_f32(c[1], src);
    d2 = sm86_shfl_idx_f32(c[2], src);
    d3 = sm86_shfl_idx_f32(c[3], src);
    d4 = sm86_shfl_idx_f32(c[4], src);
    d5 = sm86_shfl_idx_f32(c[5], src);
    d6 = sm86_shfl_idx_f32(c[6], src);
    d7 = sm86_shfl_idx_f32(c[7], src);

    bool b0 = (lane & 4u) != 0;
    float s0 = sm86_shfl_xor_f32(b0 ? d0 : d1, 4u);
    float s1 = sm86_shfl_xor_f32(b0 ? d2 : d3, 4u);
    float s2 = sm86_shfl_xor_f32(b0 ? d4 : d5, 4u);
    float s3 = sm86_shfl_xor_f32(b0 ? d6 : d7, 4u);
    d0 = b0 ? s0 : d0; d1 = b0 ? d1 : s0;
    d2 = b0 ? s1 : d2; d3 = b0 ? d3 : s1;
    d4 = b0 ? s2 : d4; d5 = b0 ? d5 : s2;
    d6 = b0 ? s3 : d6; d7 = b0 ? d7 : s3;

    bool b1 = (lane & 8u) != 0;
    float t0 = sm86_shfl_xor_f32(b1 ? d0 : d2, 8u);
    float t1 = sm86_shfl_xor_f32(b1 ? d1 : d3, 8u);
    float t2 = sm86_shfl_xor_f32(b1 ? d4 : d6, 8u);
    float t3 = sm86_shfl_xor_f32(b1 ? d5 : d7, 8u);
    d0 = b1 ? t0 : d0; d2 = b1 ? d2 : t0;
    d1 = b1 ? t1 : d1; d3 = b1 ? d3 : t1;
    d4 = b1 ? t2 : d4; d6 = b1 ? d6 : t2;
    d5 = b1 ? t3 : d5; d7 = b1 ? d7 : t3;

    bool b2 = (lane & 16u) != 0;
    float u0 = sm86_shfl_xor_f32(b2 ? d0 : d4, 16u);
    float u1 = sm86_shfl_xor_f32(b2 ? d1 : d5, 16u);
    float u2 = sm86_shfl_xor_f32(b2 ? d2 : d6, 16u);
    float u3 = sm86_shfl_xor_f32(b2 ? d3 : d7, 16u);
    d0 = b2 ? u0 : d0; d4 = b2 ? d4 : u0;
    d1 = b2 ? u1 : d1; d5 = b2 ? d5 : u1;
    d2 = b2 ? u2 : d2; d6 = b2 ? d6 : u2;
    d3 = b2 ? u3 : d3; d7 = b2 ? d7 : u3;
}

SM86_DEV sm86_f8 sm86_ampere_d_to_rdna4(float d0, float d1, float d2, float d3,
                                        float d4, float d5, float d6, float d7, sm86_u32 lane) {
    bool b0 = (lane & 4u) != 0;
    float s0 = sm86_shfl_xor_f32(b0 ? d0 : d1, 4u);
    float s1 = sm86_shfl_xor_f32(b0 ? d2 : d3, 4u);
    float s2 = sm86_shfl_xor_f32(b0 ? d4 : d5, 4u);
    float s3 = sm86_shfl_xor_f32(b0 ? d6 : d7, 4u);
    d0 = b0 ? s0 : d0; d1 = b0 ? d1 : s0;
    d2 = b0 ? s1 : d2; d3 = b0 ? d3 : s1;
    d4 = b0 ? s2 : d4; d5 = b0 ? d5 : s2;
    d6 = b0 ? s3 : d6; d7 = b0 ? d7 : s3;

    bool b1 = (lane & 8u) != 0;
    float t0 = sm86_shfl_xor_f32(b1 ? d0 : d2, 8u);
    float t1 = sm86_shfl_xor_f32(b1 ? d1 : d3, 8u);
    float t2 = sm86_shfl_xor_f32(b1 ? d4 : d6, 8u);
    float t3 = sm86_shfl_xor_f32(b1 ? d5 : d7, 8u);
    d0 = b1 ? t0 : d0; d2 = b1 ? d2 : t0;
    d1 = b1 ? t1 : d1; d3 = b1 ? d3 : t1;
    d4 = b1 ? t2 : d4; d6 = b1 ? d6 : t2;
    d5 = b1 ? t3 : d5; d7 = b1 ? d7 : t3;

    bool b2 = (lane & 16u) != 0;
    float u0 = sm86_shfl_xor_f32(b2 ? d0 : d4, 16u);
    float u1 = sm86_shfl_xor_f32(b2 ? d1 : d5, 16u);
    float u2 = sm86_shfl_xor_f32(b2 ? d2 : d6, 16u);
    float u3 = sm86_shfl_xor_f32(b2 ? d3 : d7, 16u);
    d0 = b2 ? u0 : d0; d4 = b2 ? d4 : u0;
    d1 = b2 ? u1 : d1; d5 = b2 ? d5 : u1;
    d2 = b2 ? u2 : d2; d6 = b2 ? d6 : u2;
    d3 = b2 ? u3 : d3; d7 = b2 ? d7 : u3;

    sm86_u32 src = (lane & 24u) | ((lane & 1u) << 2) | ((lane >> 1) & 3u);
    return sm86_f8{
        sm86_shfl_idx_f32(d0, src),
        sm86_shfl_idx_f32(d1, src),
        sm86_shfl_idx_f32(d2, src),
        sm86_shfl_idx_f32(d3, src),
        sm86_shfl_idx_f32(d4, src),
        sm86_shfl_idx_f32(d5, src),
        sm86_shfl_idx_f32(d6, src),
        sm86_shfl_idx_f32(d7, src)
    };
}

SM86_DEV sm86_f8 __builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(sm86_h8 a, sm86_h8 b, sm86_f8 c) {
    sm86_u32 lane = sm86_lane_id();
    sm86_u4 ua = __builtin_bit_cast(sm86_u4, a);
    sm86_u4 ub = __builtin_bit_cast(sm86_u4, b);
    sm86_u32 ra0, ra1, ra2, ra3, rb0, rb1, rb2, rb3;
    sm86_frag_butterfly(ua, ra0, ra1, ra2, ra3, lane);
    sm86_frag_butterfly(ub, rb0, rb1, rb2, rb3, lane);

    float ac0, ac1, ac2, ac3, ac4, ac5, ac6, ac7;
    if (__builtin_constant_p(c[0]) && __builtin_constant_p(c[1]) &&
        __builtin_constant_p(c[2]) && __builtin_constant_p(c[3]) &&
        __builtin_constant_p(c[4]) && __builtin_constant_p(c[5]) &&
        __builtin_constant_p(c[6]) && __builtin_constant_p(c[7]) &&
        c[0] == 0.f && c[1] == 0.f && c[2] == 0.f && c[3] == 0.f &&
        c[4] == 0.f && c[5] == 0.f && c[6] == 0.f && c[7] == 0.f) {
        ac0 = 0.f; ac1 = 0.f; ac2 = 0.f; ac3 = 0.f;
        ac4 = 0.f; ac5 = 0.f; ac6 = 0.f; ac7 = 0.f;
    } else {
        sm86_rdna4_c_to_ampere(c, ac0, ac1, ac2, ac3, ac4, ac5, ac6, ac7, lane);
    }

    float ad0, ad1, ad2, ad3, ad4, ad5, ad6, ad7;
    asm volatile(
        "mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32 "
        "{%0, %1, %2, %3}, {%4, %5, %6, %7}, {%8, %9}, {%10, %11, %12, %13};"
        : "=f"(ad0), "=f"(ad1), "=f"(ad4), "=f"(ad5)
        : "r"(ra0), "r"(ra1), "r"(ra2), "r"(ra3),
          "r"(rb0), "r"(rb2),
          "f"(ac0), "f"(ac1), "f"(ac4), "f"(ac5)
    );
    asm volatile(
        "mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32 "
        "{%0, %1, %2, %3}, {%4, %5, %6, %7}, {%8, %9}, {%10, %11, %12, %13};"
        : "=f"(ad2), "=f"(ad3), "=f"(ad6), "=f"(ad7)
        : "r"(ra0), "r"(ra1), "r"(ra2), "r"(ra3),
          "r"(rb1), "r"(rb3),
          "f"(ac2), "f"(ac3), "f"(ac6), "f"(ac7)
    );

    return sm86_ampere_d_to_rdna4(ad0, ad1, ad2, ad3, ad4, ad5, ad6, ad7, lane);
}

SM86_DEV sm86_u32 sm86_e4m3x2_to_f16x2(sm86_u32 pair_bytes) {
    sm86_u32 lo = (sm86_u32)sm86_e4m3_to_f16_bits(pair_bytes & 0xffu);
    sm86_u32 hi = (sm86_u32)sm86_e4m3_to_f16_bits((pair_bytes >> 8) & 0xffu);
    return lo | (hi << 16);
}

SM86_DEV sm86_f8 __builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(sm86_i2 a, sm86_i2 b, sm86_f8 c) {
    sm86_u32 a0 = (sm86_u32)a[0], a1 = (sm86_u32)a[1];
    sm86_u32 b0 = (sm86_u32)b[0], b1 = (sm86_u32)b[1];
    sm86_u4 ua = {
        sm86_e4m3x2_to_f16x2(a0),
        sm86_e4m3x2_to_f16x2(a0 >> 16),
        sm86_e4m3x2_to_f16x2(a1),
        sm86_e4m3x2_to_f16x2(a1 >> 16)
    };
    sm86_u4 ub = {
        sm86_e4m3x2_to_f16x2(b0),
        sm86_e4m3x2_to_f16x2(b0 >> 16),
        sm86_e4m3x2_to_f16x2(b1),
        sm86_e4m3x2_to_f16x2(b1 >> 16)
    };
    return __builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(
        __builtin_bit_cast(sm86_h8, ua),
        __builtin_bit_cast(sm86_h8, ub),
        c);
}

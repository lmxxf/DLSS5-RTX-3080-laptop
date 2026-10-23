#pragma once

// ============================================================================
// sm86_compat.h — RDNA4 Wave32 (gfx1201) -> NVIDIA Ampere (sm_86) Device Layer
// V2 Optimized:
//   1. Branchless prmt.b32 + mul.rn.f16x2 (0x5c005c00) E4M3x8 -> F16x8 decode
//   2. 4-shfl XOR-Benes network for A/B fragments (8 shfl/WMMA, down from 16)
//   3. 8-shfl XOR-Benes network for C/D fragments (down from 20 shfl each)
//   4. SSA IR algebraic cancellation (__sm86_c_to_ampere / __sm86_d_to_rdna4)
//      eliminating intermediate C/D shuffles across unrolled & loop-PHI K-loops
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

SM86_DEV float __builtin_amdgcn_logf(float x) {
    float r;
    asm("lg2.approx.ftz.f32 %0, %1;" : "=f"(r) : "f"(x));
    return r;
}

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

SM86_DEV float __builtin_amdgcn_fmed3f(float a, float b, float c) {
    float hi, r;
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
SM86_DEV float __builtin_amdgcn_cvt_f32_fp8(int src, int byte_sel) {
    sm86_u32 b = (((sm86_u32)src) >> (8 * (byte_sel & 3))) & 0xffu;
    sm86_u32 a = b & 0x7fu;
    sm86_u32 raw = ((b & 0x80u) << 8) | ((a == 0x7fu) ? 0x7e00u : (a << 7));
    sm86_u32 sc = 0x5c005c00u;
    asm("mul.rn.f16x2 %0, %0, %1;" : "+r"(raw) : "r"(sc));
    return sm86_v_cvt_f32_f16(raw);
}

// Vectorized branchless unpacking of 8 E4M3 bytes (sm86_i2) -> 8 FP16 values (sm86_u4)
// Uses 4 prmt.b32 + 4 mul.rn.f16x2 (0x5c005c00), zero branches!
SM86_DEV sm86_u4 sm86_unpack_e4m3x8(sm86_i2 a) {
    sm86_u32 a0 = (sm86_u32)a[0], a1 = (sm86_u32)a[1];
    sm86_u32 u0, u1, u2, u3;
    asm("prmt.b32 %0, %4, 0, 0x1404;\n\t"
        "prmt.b32 %1, %4, 0, 0x3424;\n\t"
        "prmt.b32 %2, %5, 0, 0x1404;\n\t"
        "prmt.b32 %3, %5, 0, 0x3424;"
        : "=&r"(u0), "=&r"(u1), "=&r"(u2), "=r"(u3) : "r"(a0), "r"(a1));
    u0 = (u0 & 0x80008000u) | ((u0 & 0x7f007f00u) >> 1);
    u1 = (u1 & 0x80008000u) | ((u1 & 0x7f007f00u) >> 1);
    u2 = (u2 & 0x80008000u) | ((u2 & 0x7f007f00u) >> 1);
    u3 = (u3 & 0x80008000u) | ((u3 & 0x7f007f00u) >> 1);
    sm86_u32 scale = 0x5c005c00u;
    asm("mul.rn.f16x2 %0, %0, %4;\n\t"
        "mul.rn.f16x2 %1, %1, %4;\n\t"
        "mul.rn.f16x2 %2, %2, %4;\n\t"
        "mul.rn.f16x2 %3, %3, %4;"
        : "+r"(u0), "+r"(u1), "+r"(u2), "+r"(u3) : "r"(scale));
    return sm86_u4{u0, u1, u2, u3};
}

SM86_DEV sm86_u32 sm86_f32_to_e4m3_byte(float x) {
    sm86_u32 b = __builtin_bit_cast(sm86_u32, x);
    sm86_u32 s = (b >> 24) & 0x80u;
    sm86_u32 a = b & 0x7fffffffu;
    float magic;
    asm("add.rn.f32 %0, %1, 0f46800000;" : "=f"(magic) : "f"(__builtin_bit_cast(float, a)));
    sm86_u32 sub = __builtin_bit_cast(sm86_u32, magic) & 0xffu;
    sm86_u32 r = a + 0x7ffffu + ((a >> 20) & 1u);
    sm86_u32 norm = (r >= 0x43e00000u) ? 0x7eu : ((r >> 20) - 0x3c0u);
    sm86_u32 mag = (a < 0x3c800000u) ? sub : ((a >= 0x7f800000u) ? 0x7fu : norm);
    return s | mag;
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
// 4-shfl XOR-Benes Network for A and B fragments (down from 8 shfl!)
SM86_DEV void sm86_frag_benes4(sm86_u4 u, sm86_u32 &r0, sm86_u32 &r1, sm86_u32 &r2, sm86_u32 &r3, sm86_u32 lane) {
    sm86_u32 u0 = u[0], u1 = u[1], u2 = u[2], u3 = u[3];
    bool p0 = (lane & 8u) != 0;
    sm86_u32 a0 = p0 ? u1 : u0, a1 = p0 ? u0 : u1;
    sm86_u32 a2 = p0 ? u3 : u2, a3 = p0 ? u2 : u3;
    bool p1 = (lane & 16u) != 0;
    sm86_u32 w0 = p1 ? a2 : a0, w1 = p1 ? a3 : a1;
    sm86_u32 w2 = p1 ? a0 : a2, w3 = p1 ? a1 : a3;

    sm86_u32 base = (lane >> 2) ^ ((lane & 3u) << 3);
    sm86_u32 v0 = sm86_shfl_idx_u32(w0, base);
    sm86_u32 v1 = sm86_shfl_idx_u32(w1, base ^ 8u);
    sm86_u32 v2 = sm86_shfl_idx_u32(w2, base ^ 16u);
    sm86_u32 v3 = sm86_shfl_idx_u32(w3, base ^ 24u);

    bool q0 = (lane & 1u) != 0;
    sm86_u32 b0 = q0 ? v1 : v0, b1 = q0 ? v0 : v1;
    sm86_u32 b2 = q0 ? v3 : v2, b3 = q0 ? v2 : v3;
    bool q1 = (lane & 2u) != 0;
    r0 = q1 ? b2 : b0;
    r1 = q1 ? b3 : b1;
    r2 = q1 ? b0 : b2;
    r3 = q1 ? b1 : b3;
}

// 8-shfl XOR-Benes Network for C (RDNA4 -> Ampere) and D (Ampere -> RDNA4)
// Marked `noinline, const` during initial Clang IR emission so SSA pass cancels
// back-to-back C/D shuffles across K-loops; converted to `alwaysinline` before opt -O3!
extern "C" __attribute__((device, noinline))
sm86_f8 __sm86_c_to_ampere(sm86_f8 c) __asm__("__sm86_c_to_ampere");

extern "C" __attribute__((device, noinline))
sm86_f8 __sm86_d_to_rdna4(sm86_f8 d) __asm__("__sm86_d_to_rdna4");

extern "C" __attribute__((device, noinline))
sm86_f8 __sm86_c_to_ampere(sm86_f8 c) {
    sm86_u32 lane = sm86_lane_id();
    float v0 = c[0], v1 = c[1], v2 = c[2], v3 = c[3], v4 = c[4], v5 = c[5], v6 = c[6], v7 = c[7];
    bool p0 = (lane & 1u) != 0;
    float a0 = p0 ? v1 : v0, a1 = p0 ? v0 : v1, a2 = p0 ? v3 : v2, a3 = p0 ? v2 : v3;
    float a4 = p0 ? v5 : v4, a5 = p0 ? v4 : v5, a6 = p0 ? v7 : v6, a7 = p0 ? v6 : v7;
    bool p1 = (lane & 8u) != 0;
    float b0 = p1 ? a2 : a0, b1 = p1 ? a3 : a1, b2 = p1 ? a0 : a2, b3 = p1 ? a1 : a3;
    float b4 = p1 ? a6 : a4, b5 = p1 ? a7 : a5, b6 = p1 ? a4 : a6, b7 = p1 ? a5 : a7;
    bool p2 = (lane & 16u) != 0;
    float w0 = p2 ? b4 : b0, w1 = p2 ? b5 : b1, w2 = p2 ? b6 : b2, w3 = p2 ? b7 : b3;
    float w4 = p2 ? b0 : b4, w5 = p2 ? b1 : b5, w6 = p2 ? b2 : b6, w7 = p2 ? b3 : b7;

    sm86_u32 base = (lane & 24u) | ((lane & 3u) << 1) | ((lane >> 2) & 1u);
    float x0 = sm86_shfl_idx_f32(w0, base);
    float x1 = sm86_shfl_idx_f32(w1, base ^ 1u);
    float x2 = sm86_shfl_idx_f32(w2, base ^ 8u);
    float x3 = sm86_shfl_idx_f32(w3, base ^ 9u);
    float x4 = sm86_shfl_idx_f32(w4, base ^ 16u);
    float x5 = sm86_shfl_idx_f32(w5, base ^ 17u);
    float x6 = sm86_shfl_idx_f32(w6, base ^ 24u);
    float x7 = sm86_shfl_idx_f32(w7, base ^ 25u);

    bool q0 = (lane & 4u) != 0;
    float y0 = q0 ? x1 : x0, y1 = q0 ? x0 : x1, y2 = q0 ? x3 : x2, y3 = q0 ? x2 : x3;
    float y4 = q0 ? x5 : x4, y5 = q0 ? x4 : x5, y6 = q0 ? x7 : x6, y7 = q0 ? x6 : x7;
    bool q1 = (lane & 8u) != 0;
    float z0 = q1 ? y2 : y0, z1 = q1 ? y3 : y1, z2 = q1 ? y0 : y2, z3 = q1 ? y1 : y3;
    float z4 = q1 ? y6 : y4, z5 = q1 ? y7 : y5, z6 = q1 ? y4 : y6, z7 = q1 ? y5 : y7;
    bool q2 = (lane & 16u) != 0;
    return sm86_f8{
        q2 ? z4 : z0, q2 ? z5 : z1, q2 ? z6 : z2, q2 ? z7 : z3,
        q2 ? z0 : z4, q2 ? z1 : z5, q2 ? z2 : z6, q2 ? z3 : z7
    };
}

extern "C" __attribute__((device, noinline))
sm86_f8 __sm86_d_to_rdna4(sm86_f8 d) {
    sm86_u32 lane = sm86_lane_id();
    float d0 = d[0], d1 = d[1], d2 = d[2], d3 = d[3], d4 = d[4], d5 = d[5], d6 = d[6], d7 = d[7];
    bool q0 = (lane & 4u) != 0;
    float a0 = q0 ? d1 : d0, a1 = q0 ? d0 : d1, a2 = q0 ? d3 : d2, a3 = q0 ? d2 : d3;
    float a4 = q0 ? d5 : d4, a5 = q0 ? d4 : d5, a6 = q0 ? d7 : d6, a7 = q0 ? d6 : d7;
    bool q1 = (lane & 8u) != 0;
    float b0 = q1 ? a2 : a0, b1 = q1 ? a3 : a1, b2 = q1 ? a0 : a2, b3 = q1 ? a1 : a3;
    float b4 = q1 ? a6 : a4, b5 = q1 ? a7 : a5, b6 = q1 ? a4 : a6, b7 = q1 ? a5 : a7;
    bool q2 = (lane & 16u) != 0;
    float w0 = q2 ? b4 : b0, w1 = q2 ? b5 : b1, w2 = q2 ? b6 : b2, w3 = q2 ? b7 : b3;
    float w4 = q2 ? b0 : b4, w5 = q2 ? b1 : b5, w6 = q2 ? b2 : b6, w7 = q2 ? b3 : b7;

    sm86_u32 base = (lane & 24u) | ((lane & 1u) << 2) | ((lane >> 1) & 3u);
    float x0 = sm86_shfl_idx_f32(w0, base);
    float x1 = sm86_shfl_idx_f32(w1, base ^ 4u);
    float x2 = sm86_shfl_idx_f32(w2, base ^ 8u);
    float x3 = sm86_shfl_idx_f32(w3, base ^ 12u);
    float x4 = sm86_shfl_idx_f32(w4, base ^ 16u);
    float x5 = sm86_shfl_idx_f32(w5, base ^ 20u);
    float x6 = sm86_shfl_idx_f32(w6, base ^ 24u);
    float x7 = sm86_shfl_idx_f32(w7, base ^ 28u);

    bool p0 = (lane & 1u) != 0;
    float y0 = p0 ? x1 : x0, y1 = p0 ? x0 : x1, y2 = p0 ? x3 : x2, y3 = p0 ? x2 : x3;
    float y4 = p0 ? x5 : x4, y5 = p0 ? x4 : x5, y6 = p0 ? x7 : x6, y7 = p0 ? x6 : x7;
    bool p1 = (lane & 8u) != 0;
    float z0 = p1 ? y2 : y0, z1 = p1 ? y3 : y1, z2 = p1 ? y0 : y2, z3 = p1 ? y1 : y3;
    float z4 = p1 ? y6 : y4, z5 = p1 ? y7 : y5, z6 = p1 ? y4 : y6, z7 = p1 ? y5 : y7;
    bool p2 = (lane & 16u) != 0;
    return sm86_f8{
        p2 ? z4 : z0, p2 ? z5 : z1, p2 ? z6 : z2, p2 ? z7 : z3,
        p2 ? z0 : z4, p2 ? z1 : z5, p2 ? z2 : z6, p2 ? z3 : z7
    };
}

// Pure operand preparation functions marked `noinline, const` during initial Clang IR
// emission so LLVM GVN / EarlyCSE / LICM automatically deduplicates shared A or B
// fragments across multi-tile WMMAs and hoists loop-invariant fragments out of loops!
extern "C" __attribute__((device, noinline))
sm86_u4 __sm86_prep_f16(sm86_h8 x) __asm__("__sm86_prep_f16");

extern "C" __attribute__((device, noinline))
sm86_u4 __sm86_prep_fp8(sm86_i2 x) __asm__("__sm86_prep_fp8");

extern "C" __attribute__((device, noinline))
sm86_u4 __sm86_prep_f16(sm86_h8 x) {
    sm86_u32 lane = sm86_lane_id();
    sm86_u4 ux = __builtin_bit_cast(sm86_u4, x);
    sm86_u32 r0, r1, r2, r3;
    sm86_frag_benes4(ux, r0, r1, r2, r3, lane);
    return sm86_u4{r0, r1, r2, r3};
}

// Shuffle-Before-Unpack: shuffles two 32-bit words first (only 6 selp instead of 16!), then unpacks 4 E4M3 pairs to F16x2
extern "C" __attribute__((device, noinline))
sm86_u4 __sm86_prep_fp8(sm86_i2 a) {
    sm86_u32 lane = sm86_lane_id();
    sm86_u32 u0 = (sm86_u32)a[0], u1 = (sm86_u32)a[1];
    bool p1 = (lane & 16u) != 0;
    sm86_u32 w0 = p1 ? u1 : u0;
    sm86_u32 w1 = p1 ? u0 : u1;

    sm86_u32 base = (lane >> 2) ^ ((lane & 2u) << 3);
    sm86_u32 v0 = sm86_shfl_idx_u32(w0, base);
    sm86_u32 v1 = sm86_shfl_idx_u32(w0, base ^ 8u);
    sm86_u32 v2 = sm86_shfl_idx_u32(w1, base ^ 16u);
    sm86_u32 v3 = sm86_shfl_idx_u32(w1, base ^ 24u);

    bool q1 = (lane & 2u) != 0;
    sm86_u32 b0 = q1 ? v2 : v0;
    sm86_u32 b1 = q1 ? v3 : v1;
    sm86_u32 b2 = q1 ? v0 : v2;
    sm86_u32 b3 = q1 ? v1 : v3;

    sm86_u32 sel = (lane & 1u) ? 0x3424u : 0x1404u;
    sm86_u32 r0, r1, r2, r3;
    asm("prmt.b32 %0, %4, 0, %8;\n\t"
        "prmt.b32 %1, %5, 0, %8;\n\t"
        "prmt.b32 %2, %6, 0, %8;\n\t"
        "prmt.b32 %3, %7, 0, %8;"
        : "=&r"(r0), "=&r"(r1), "=&r"(r2), "=r"(r3)
        : "r"(b0), "r"(b1), "r"(b2), "r"(b3), "r"(sel));
    r0 = (r0 & 0x80008000u) | ((r0 & 0x7f007f00u) >> 1);
    r1 = (r1 & 0x80008000u) | ((r1 & 0x7f007f00u) >> 1);
    r2 = (r2 & 0x80008000u) | ((r2 & 0x7f007f00u) >> 1);
    r3 = (r3 & 0x80008000u) | ((r3 & 0x7f007f00u) >> 1);
    sm86_u32 scale = 0x5c005c00u;
    asm("mul.rn.f16x2 %0, %0, %4;\n\t"
        "mul.rn.f16x2 %1, %1, %4;\n\t"
        "mul.rn.f16x2 %2, %2, %4;\n\t"
        "mul.rn.f16x2 %3, %3, %4;"
        : "+r"(r0), "+r"(r1), "+r"(r2), "+r"(r3) : "r"(scale));
    return sm86_u4{r0, r1, r2, r3};
}

// Pre-shuffle 8-byte `i2` from RDNA4 layout into 8-byte Ampere layout for Q/K/V/prob staging
SM86_DEV sm86_i2 sm86_preshuffle_fp8(sm86_i2 a) {
    sm86_u32 lane = sm86_lane_id();
    sm86_u32 u0 = (sm86_u32)a[0], u1 = (sm86_u32)a[1];
    bool p1 = (lane & 16u) != 0;
    sm86_u32 w0 = p1 ? u1 : u0;
    sm86_u32 w1 = p1 ? u0 : u1;

    sm86_u32 base = (lane >> 2) ^ ((lane & 2u) << 3);
    sm86_u32 v0 = sm86_shfl_idx_u32(w0, base);
    sm86_u32 v1 = sm86_shfl_idx_u32(w0, base ^ 8u);
    sm86_u32 v2 = sm86_shfl_idx_u32(w1, base ^ 16u);
    sm86_u32 v3 = sm86_shfl_idx_u32(w1, base ^ 24u);

    bool q1 = (lane & 2u) != 0;
    sm86_u32 b0 = q1 ? v2 : v0;
    sm86_u32 b1 = q1 ? v3 : v1;
    sm86_u32 b2 = q1 ? v0 : v2;
    sm86_u32 b3 = q1 ? v1 : v3;

    sm86_u32 sel = (lane & 1u) ? 0x7632u : 0x5410u;
    sm86_u32 o0, o1;
    asm("prmt.b32 %0, %2, %3, %6;\n\t"
        "prmt.b32 %1, %4, %5, %6;"
        : "=&r"(o0), "=r"(o1)
        : "r"(b0), "r"(b1), "r"(b2), "r"(b3), "r"(sel));
    return sm86_i2{(int)o0, (int)o1};
}

SM86_DEV sm86_f8 sm86_mma_prepared_core(sm86_u4 ra, sm86_u4 rb, sm86_f8 ac) {
    float ad0, ad1, ad2, ad3, ad4, ad5, ad6, ad7;
    asm volatile(
        "mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32 "
        "{%0, %1, %2, %3}, {%4, %5, %6, %7}, {%8, %9}, {%10, %11, %12, %13};"
        : "=f"(ad0), "=f"(ad1), "=f"(ad4), "=f"(ad5)
        : "r"(ra[0]), "r"(ra[1]), "r"(ra[2]), "r"(ra[3]),
          "r"(rb[0]), "r"(rb[2]),
          "f"(ac[0]), "f"(ac[1]), "f"(ac[4]), "f"(ac[5])
    );
    asm volatile(
        "mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32 "
        "{%0, %1, %2, %3}, {%4, %5, %6, %7}, {%8, %9}, {%10, %11, %12, %13};"
        : "=f"(ad2), "=f"(ad3), "=f"(ad6), "=f"(ad7)
        : "r"(ra[0]), "r"(ra[1]), "r"(ra[2]), "r"(ra[3]),
          "r"(rb[1]), "r"(rb[3]),
          "f"(ac[2]), "f"(ac[3]), "f"(ac[6]), "f"(ac[7])
    );
    return sm86_f8{ad0, ad1, ad2, ad3, ad4, ad5, ad6, ad7};
}

SM86_DEV sm86_f8 __builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12(sm86_h8 a, sm86_h8 b, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(__sm86_prep_f16(a), __sm86_prep_f16(b), ac);
    return __sm86_d_to_rdna4(ad);
}

SM86_DEV sm86_f8 __builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(sm86_i2 a, sm86_i2 b, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(__sm86_prep_fp8(a), __sm86_prep_fp8(b), ac);
    return __sm86_d_to_rdna4(ad);
}

// Zero-shuffle WMMA for pre-shuffled Q/K/V/prob `i2` fragments!
SM86_DEV sm86_f8 sm86_wmma_fp8_preshuffled_ab(sm86_i2 pa, sm86_i2 pb, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(sm86_unpack_e4m3x8(pa), sm86_unpack_e4m3x8(pb), ac);
    return __sm86_d_to_rdna4(ad);
}

SM86_DEV sm86_f8 sm86_wmma_fp8_prepped_b(sm86_i2 a, sm86_u4 rb, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(__sm86_prep_fp8(a), rb, ac);
    return __sm86_d_to_rdna4(ad);
}

SM86_DEV sm86_f8 sm86_wmma_fp8_preshuffled_b(sm86_i2 a, sm86_i2 pb, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(__sm86_prep_fp8(a), sm86_unpack_e4m3x8(pb), ac);
    return __sm86_d_to_rdna4(ad);
}

SM86_DEV sm86_f8 sm86_wmma_fp8_preshuffled_a(sm86_i2 pa, sm86_i2 b, sm86_f8 c) {
    sm86_f8 ac = __sm86_c_to_ampere(c);
    sm86_f8 ad = sm86_mma_prepared_core(sm86_unpack_e4m3x8(pa), __sm86_prep_fp8(b), ac);
    return __sm86_d_to_rdna4(ad);
}

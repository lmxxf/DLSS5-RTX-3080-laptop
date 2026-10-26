#pragma once
// CUDA-only V3 static weights. References remain narrow until the consuming MMA.
struct cw_half_ref { const unsigned char* p; };
struct cw_half_pair { cw_half_ref lo, hi; };
SM86_DEV cw_half_pair cw_half_matrix16(const float*w,unsigned tail,unsigned byte_offset){
 const unsigned char*p=reinterpret_cast<const unsigned char*>(w)+tail+2*byte_offset;
 return {{p},{p+16}};
}
SM86_DEV sm86_u4 cw_half_load(cw_half_ref w){
 sm86_u4 v;
 asm volatile("ld.global.nc.v4.u32 {%0,%1,%2,%3}, [%4];" : "=r"(v[0]),"=r"(v[1]),"=r"(v[2]),"=r"(v[3]) : "l"(w.p) : "memory");
 return v;
}
SM86_DEV sm86_f8 sm86_c32_half_a(cw_half_ref w,sm86_i2 b,sm86_f8 c){
 return __sm86_d_to_rdna4(sm86_mma_prepared_core(cw_half_load(w),__sm86_unpack_fp8(b),__sm86_c_to_ampere(c)));
}
SM86_DEV sm86_f8 sm86_c32_half_b(sm86_i2 a,cw_half_ref w,sm86_f8 c){
 return __sm86_d_to_rdna4(sm86_mma_prepared_core(__sm86_unpack_fp8(a),cw_half_load(w),__sm86_c_to_ampere(c)));
}

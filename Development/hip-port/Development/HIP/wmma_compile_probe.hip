// Compile-only gfx1201 probe; launch requires exactly one wave (32 threads).
// FP8 E4M3 bytes enter as two packed int32 words per lane for each operand.
typedef int int2 __attribute__((ext_vector_type(2)));
typedef float float8 __attribute__((ext_vector_type(8)));
extern "C" __attribute__((global)) void wmma_probe(const int* packed, float* out) {
 unsigned lane=__builtin_amdgcn_workitem_id_x();
 int2 a={packed[lane*4],packed[lane*4+1]};
 int2 b={packed[lane*4+2],packed[lane*4+3]};
 float8 c={0,0,0,0,0,0,0,0};
 float8 d=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,c);
 for(unsigned i=0;i<8;i++)out[lane*8+i]=d[i];
}

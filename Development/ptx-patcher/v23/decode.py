"""Two byte-sign-replicating PRMTs replace masked sign arithmetic."""
def decode(register,first,second):
 return [f'prmt.b32 {first}, {register}, {register}, 0xa280;',f'and.b32 {first}, {first}, 0x017f017f;',f'shl.b32 {first}, {first}, 7;',f'mul.rn.f16x2 {first}, {first}, dlssnr_fp8_scale;',f'prmt.b32 {second}, {register}, {register}, 0xb391;',f'and.b32 {second}, {second}, 0x017f017f;',f'shl.b32 {second}, {second}, 7;',f'mul.rn.f16x2 {second}, {second}, dlssnr_fp8_scale;']

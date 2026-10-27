"""V2.5: keep even-byte PRMT, route aligned odd-byte signs through LOP3."""
def decode(register,first,second):
 return [f'prmt.b32 {first}, {register}, {register}, 0xa280;',f'and.b32 {first}, {first}, 0x017f017f;',f'shl.b32 {first}, {first}, 7;',f'mul.rn.f16x2 {first}, {first}, dlssnr_fp8_scale;',f'and.b32 {second}, {register}, 0x7f007f00;',f'shr.u32 {second}, {second}, 1;',f'lop3.b32 {second}, {register}, 0x80008000, {second}, 0xea;',f'mul.rn.f16x2 {second}, {second}, dlssnr_fp8_scale;']

MODE='exact'
def declarations():
 return ['.reg .b32 v29_a, v29_t;']+(['.reg .b32 v29_y, v29_z;'] if MODE=='exact' else [])
def pack(source,destination):
 a='v29_a';y='v29_y' if MODE=='exact' else a
 lines=[f'and.b32 {a}, {source}, 0x7fff7fff;','mov.b32 v29_t, 0x5f005f00;',f'min.f16x2 {a}, {a}, v29_t;','mov.b32 v29_t, 0x1c001c00;',f'mul.rn.f16x2 {y}, {a}, v29_t;']
 if MODE=='exact':lines+=['add.u32 v29_z, v29_a, 0x003f003f;','shr.u32 v29_t, v29_y, 1;','lop3.b32 v29_t, v29_a, v29_z, v29_t, 0x8e;','shr.u32 v29_t, v29_t, 5;']
 else:lines+=['shr.u32 v29_t, v29_a, 6;']
 return lines+['and.b32 v29_t, v29_t, 0x00020002;',f'shl.b32 {y}, {y}, 1;',f'add.u32 {y}, {y}, 0x007e007e;',f'add.u32 {y}, {y}, v29_t;',f'lop3.b32 {y}, {source}, {y}, 0x7f007f00, 0xd8;',f'prmt.b32 {y}, {y}, 0, 0x4431;',f'cvt.u16.u32 {destination}, {y};']

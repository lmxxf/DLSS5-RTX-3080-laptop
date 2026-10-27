"""V2.2 isolated factors; baseline generator remains available for differential tests."""

def declarations():
 return ['.reg .b32 dlssnr_v22_a, dlssnr_v22_sub, dlssnr_v22_n, dlssnr_v22_t, dlssnr_v22_mask;']

def pack(source,destination):
 # Clamp magnitudes before packed bias/rounding; neither 16-bit lane carries
 # into its neighbor. set produces two 0xffff masks; lop3 selects each lane.
 # Signed zero and nonfinite behavior are checked against the legacy emitter.
 return [
 f'and.b32 dlssnr_v22_a, {source}, 0x7fff7fff;',
 'mov.b32 dlssnr_v22_mask, 0x5f005f00;',
 'min.f16x2 dlssnr_v22_a, dlssnr_v22_a, dlssnr_v22_mask;',
 'mov.b32 dlssnr_v22_mask, 0x40004000;',
 'add.rn.f16x2 dlssnr_v22_sub, dlssnr_v22_a, dlssnr_v22_mask;',
 'shr.u32 dlssnr_v22_t, dlssnr_v22_a, 7;',
 'and.b32 dlssnr_v22_t, dlssnr_v22_t, 0x00010001;',
 'add.u32 dlssnr_v22_n, dlssnr_v22_a, 0x003f003f;',
 'add.u32 dlssnr_v22_n, dlssnr_v22_n, dlssnr_v22_t;',
 'shr.u32 dlssnr_v22_n, dlssnr_v22_n, 7;',
 'add.u32 dlssnr_v22_n, dlssnr_v22_n, 0x00c000c0;',
 'mov.b32 dlssnr_v22_mask, 0x24002400;',
 'set.lt.u32.f16x2 dlssnr_v22_mask, dlssnr_v22_a, dlssnr_v22_mask;',
 # LUT implements mask ? sub : norm (a=sub, b=norm, c=mask).
 'lop3.b32 dlssnr_v22_n, dlssnr_v22_sub, dlssnr_v22_n, dlssnr_v22_mask, 0xe4;',
 'and.b32 dlssnr_v22_n, dlssnr_v22_n, 0x007f007f;',
 f'shr.u32 dlssnr_v22_t, {source}, 8;',
 'and.b32 dlssnr_v22_t, dlssnr_v22_t, 0x00800080;',
 'or.b32 dlssnr_v22_n, dlssnr_v22_n, dlssnr_v22_t;',
 'prmt.b32 dlssnr_v22_n, dlssnr_v22_n, 0, 0x4420;',
 f'cvt.u16.u32 {destination}, dlssnr_v22_n;',
 ]

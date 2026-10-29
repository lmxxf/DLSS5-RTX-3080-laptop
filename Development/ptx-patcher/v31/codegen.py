MODE='pack8'
def declarations():return ['.reg .b32 v31_a,v31_t;']
def pack(source,destination):
 from v29 import codegen as old
 old.MODE='fast'
 if MODE=='pack8':return [l.replace('and.b32 v29_a, '+source+', 0x7fff7fff;','abs.f16x2 v29_a, '+source+';').replace('v29_','v31_') for l in old.pack(source,destination)]
 return [f'abs.f16x2 v31_a, {source};','mov.b32 v31_t, 0x5f005f00;','min.f16x2 v31_a, v31_a, v31_t;','mov.b32 v31_t, 0x1c001c00;','mul.rn.f16x2 v31_a, v31_a, v31_t;','shl.b32 v31_a, v31_a, 1;','add.u32 v31_a, v31_a, 0x007f007f;',f'lop3.b32 v31_a, {source}, v31_a, 0x7f007f00, 0xd8;','prmt.b32 v31_a, v31_a, 0, 0x4431;',f'cvt.u16.u32 {destination}, v31_a;']
def quad(low,high,destination,bias=False):
 lines=['{','.reg .b32 vq_lo;','.reg .b32 vq_hi;','.reg .b32 vq_t;','.reg .b32 vq_reserved;']
 for src,out in [(low,'vq_lo'),(high,'vq_hi')]:lines += [l.replace('v31_a',out).replace('v31_t','vq_t') for l in pack(src,'UNUSED')[:-2]]
 return lines+[f'prmt.b32 {destination}, vq_lo, vq_hi, 0x7531;','}']

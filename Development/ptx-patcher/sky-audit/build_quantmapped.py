"""Quantize unique mapped FP16 sources, retaining mapped dead-code removal."""
from pathlib import Path
import sys,types,concurrent.futures,re
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo))
m=types.ModuleType('quant_build');sys.modules[m.__name__]=m
m.__file__=str(repo/'build_sm86_dlls.py')
s=(repo/'build_sm86_dlls.py').read_text().replace('/tmp/dlssnr-310-9-16-sm86',str(repo))
exec(compile(s,str(repo/'build_sm86_dlls.py'),'exec'),m.__dict__)
original=m.fast_render_fp8_mma_run

def quant_render(matches,packed_sources):
 text=original(matches,packed_sources)
 operands={v[g] for v in matches for g in ('a0','a1','a2','a3','b0','b1')}
 sources=sorted({s for r,(lo,hi,pos) in packed_sources.items() if r in operands and pos<matches[0].start() for s in (lo,hi)})
 if not sources:return text
 decl=['.reg .b32 qm_min, qm_max, qm_two, qm_lsb, qm_abs, qm_sub, qm_lo, qm_hi, qm_sign;', '.reg .pred qm_pl, qm_ph;']
 decl+=['.reg .b32 '+','.join(f'qm_q{i}' for i in range(len(sources)))+';']
 code=['mov.b32 qm_min, 0xdf00df00;', 'mov.b32 qm_max, 0x5f005f00;', 'mov.b32 qm_two, 0x40004000;']
 for i,src in enumerate(sources):
  q=f'qm_q{i}'
  code += [f'max.f16x2 {q}, {src}, qm_min;', f'min.f16x2 {q}, {q}, qm_max;',
   f'and.b32 qm_sign, {q}, 0x80008000;',f'and.b32 qm_abs, {q}, 0x7fff7fff;',
   'and.b32 qm_lo, qm_abs, 0xffff;','shr.u32 qm_hi, qm_abs, 16;',
   'setp.lt.u32 qm_pl, qm_lo, 0x2400;','setp.lt.u32 qm_ph, qm_hi, 0x2400;',
   # FP16 subnormal grid for E4M3 is 2^-9: add 2 RNE, subtract 2 exactly.
   'add.rn.f16x2 qm_sub, qm_abs, qm_two;', 'sub.rn.f16x2 qm_sub, qm_sub, qm_two;',
   f'shr.u32 qm_lsb, {q}, 7;', 'and.b32 qm_lsb, qm_lsb, 0x00010001;',
   'add.u32 qm_lsb, qm_lsb, 0x003f003f;',f'add.u32 {q}, {q}, qm_lsb;',f'and.b32 {q}, {q}, 0xff80ff80;',
   # Select each lane independently, preserving negative zero.
   'or.b32 qm_sub, qm_sub, qm_sign;',f'selp.b32 qm_lo, qm_sub, {q}, qm_pl;',f'selp.b32 qm_hi, qm_sub, {q}, qm_ph;',
   f'prmt.b32 {q}, qm_lo, qm_hi, 0x7610;']
  text=re.sub(r'(shfl\.sync\.idx\.b32\s+\w+,\s*)'+re.escape(src)+r'(?=,)',lambda v:v[1]+q,text)
 return text.replace('{\n','{\n'+'\n'.join(decl+code)+'\n',1)
m.fast_render_fp8_mma_run=quant_render

def work(task):return m.worker_compile_fatbin(task)
if __name__=='__main__':
 data=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes());m.dp.strip_authenticode(data);locs=m.dp.find_fatbins(data)
 out=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll').read_bytes())
 tasks=[(i,bytes(data[l.offset:l.offset+l.size]),True) for i,l in enumerate(locs)]
 count=0
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for i,fb,msg in pool.map(work,tasks):
   l=locs[i];out[l.offset:l.offset+l.size]=fb+bytes(l.size-len(fb));print(i,msg,flush=True);count+=('ELF O4' in msg)
 m.fast_update_pe_checksum(out)
 Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_quantmapped.dll').write_bytes(out)
 print('O4',count,'/',len(locs),flush=True)

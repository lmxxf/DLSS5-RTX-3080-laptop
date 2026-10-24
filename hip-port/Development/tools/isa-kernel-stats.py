#!/usr/bin/env python3
"""Per-kernel static ISA statistics from a COMGR .hsaco.s dump (rtc_compile writes <module>.hsaco.s next to the code object).
usage: isa-kernel-stats.py <module.hsaco.s> <kernel-name-substring>...
columns: instructions, wmma, VALU, SALU, LDS ops, global/scalar loads, global stores, s_wait*, s_cbranch, v_movrel, v_cvt, then the
metadata block (VGPR, SGPR, scratch bytes, LDS bytes, occupancy, code bytes). 2026-09-17: used on the C32/post/decoder and C64 kernels."""
import sys,re
def stats(path,names):
 t=open(path).read().splitlines()
 idx=[(i,l.split(':')[0]) for i,l in enumerate(t) if re.match(r'^[A-Za-z_][A-Za-z0-9_]*:',l)]
 idx.append((len(t),'END'))
 print(f"{'kernel':52s} {'instr':>6} {'wmma':>5} {'valu':>6} {'salu':>5} {'ds':>5} {'gload':>5} {'gstor':>5} {'wait':>5} {'cbr':>4} {'movrel':>6} {'cvt':>5} {'vgpr':>4} {'sgpr':>4} {'scr':>4} {'lds':>6} {'occ':>3} {'bytes':>6}")
 for k,(i,n) in enumerate(idx[:-1]):
  if not any(x in n for x in names):continue
  body=t[i:idx[k+1][0]]
  ins=[l.strip() for l in body if l.strip() and not l.strip().startswith(('//',';','.')) and not re.match(r'^[A-Za-z_.][A-Za-z0-9_.]*:',l.strip())]
  c=lambda p:sum(1 for l in ins if re.match(p,l))
  meta='\n'.join(body)
  def g(key):
   m=re.search(key+r'\s*[:=]\s*(\d+)',meta);return m.group(1) if m else '?'
  print(f"{n:52s} {len(ins):6d} {c(r'v_wmma'):5d} {c(r'v_'):6d} {c(r's_(?!wait|cbranch|branch|endpgm|nop|barrier)'):5d} {c(r'ds_'):5d} {c(r'global_load|buffer_load|s_load'):5d} {c(r'global_store|buffer_store'):5d} {c(r's_wait'):5d} {c(r's_cbranch'):4d} {c(r'v_movrel'):6d} {c(r'v_cvt'):5d} {g('NumVgprs'):>4} {g('TotalNumSgprs'):>4} {g('ScratchSize'):>4} {g('LDSByteSize'):>6} {g('Occupancy'):>3} {g('codeLenInByte'):>6}")
stats(sys.argv[1],sys.argv[2:])

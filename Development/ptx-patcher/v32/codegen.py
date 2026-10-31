"""Low/high lane-local K permutation, direct mapped halves, phase-aware backups."""
IMMEDIATE=False
SHIFT_MASK=False

def decode_half(register,dst,phase):
 scale="0x5c005c00" if IMMEDIATE else "dlssnr_fp8_scale"
 selector=("0x9180","0xb3a2")[phase]
 middle=[f"shl.b32 {dst}, {dst}, 7;",f"and.b32 {dst}, {dst}, 0xbf80bf80;"] if SHIFT_MASK else [f"and.b32 {dst}, {dst}, 0x017f017f;",f"shl.b32 {dst}, {dst}, 7;"]
 return [f"prmt.b32 {dst}, {register}, {register}, {selector};"]+middle+[f"mul.rn.f16x2 {dst}, {dst}, {scale};"]

def decode(register,first,second):
 return decode_half(register,first,0)+decode_half(register,second,1)

def render(matches,packed_sources,*,builder,audit=None):
 from ptx_mapped import mapped_at
 operands=list(dict.fromkeys(m[n] for m in matches for n in ('a0','a1','a2','a3','b0','b1')))
 mapped=mapped_at(packed_sources,matches[0].start())
 first={r:min(i for i,m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
 last={r:max(i for i,m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
 first_write={}
 for i,m in enumerate(matches):
  for s in (m['d0'],m['d1']):first_write.setdefault(s,2*i)
 # Input reads precede writes within a native K16 instruction. The FIRST K16
 # can overwrite a source needed by the SECOND K16 of this very same K32.
 last_read={}
 for i,m in enumerate(matches):
  for r in set(m[n] for n in ('a0','a1','a2','a3','b0','b1')):
   if r in mapped:
    for phase,s in enumerate(mapped[r][:2]):last_read[s]=max(last_read.get(s,-1),2*i+phase)
 save_at={s:first_write[s] for s,end in last_read.items() if s in first_write and first_write[s]<end}
 encoded=[r for r in operands if r not in mapped]
 when={(r,phase):min(2*first[r]+phase,first_write.get(r,2*first[r]+phase)) for r in encoded for phase in [0,1]}
 free=[];allocated=0;body=[];decoded={};saved={};backup_moves=0
 def alloc():
  nonlocal allocated
  if free:return free.pop()
  r=f'vlh_t{allocated}';allocated+=1;return r
 for i,m in enumerate(matches):
  for phase in [0,1]:
   step=2*i+phase
   for r in encoded:
    for half in [0,1]:
     if when[r,half]==step:
      tmp=alloc();decoded[r,half]=tmp;body.extend(decode_half(r,tmp,half))
   for source,at in save_at.items():
    if at==step:
     tmp=alloc();saved[source]=tmp;body.append(f'mov.b32 {tmp}, {source};');backup_moves+=1
   def operand(r):
    if r not in mapped:return decoded[r,phase]
    source=mapped[r][phase];return saved.get(source,source)
   aa=[operand(m[n]) for n in ('a0','a1','a2','a3')];bb=[operand(m[n]) for n in ('b0','b1')];cc=[m['c0'],m['c1']] if phase==0 else [m['d0'],m['d1']]
   body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
   for source in list(saved):
    if last_read[source]==step:free.append(saved.pop(source))
   for r,half in list(decoded):
    if 2*last[r]+half==step:free.append(decoded.pop((r,half)))
 decl=['{']
 if allocated:decl+=['.reg .b32 '+', '.join(f'vlh_t{i}' for i in range(allocated))+';']
 if encoded and not IMMEDIATE:decl+=['.reg .b32 dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale, 0x5c005c00;']
 if audit is not None:audit.append({'mma_sites':len(matches),'mapped_operands':sum(r in mapped for r in operands),'encoded_operands':len(encoded),'temporary_b32_peak':allocated,'backup_moves':backup_moves,'phase0_clobber_sources':sorted(save_at)})
 return '\n'.join(decl+body+['}'])

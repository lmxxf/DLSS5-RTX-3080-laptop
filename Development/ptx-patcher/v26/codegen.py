"""Low/high lane-local K permutation, direct mapped halves, phase-aware backups."""
def decode(register,first,second):
 out=[]
 for dst,selector in [(first,'0x9180'),(second,'0xb3a2')]:
  out += [f'prmt.b32 {dst}, {register}, {register}, {selector};',f'and.b32 {dst}, {dst}, 0x017f017f;',f'shl.b32 {dst}, {dst}, 7;',f'mul.rn.f16x2 {dst}, {dst}, dlssnr_fp8_scale;']
 return out

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
 encoded=[r for r in operands if r not in mapped];when={r:min(first[r],first_write.get(r,2*first[r])//2) for r in encoded}
 free=[];allocated=0;body=[];decoded={};saved={};backup_moves=0
 def alloc():
  nonlocal allocated
  if free:return free.pop()
  r=f'vlh_t{allocated}';allocated+=1;return r
 for i,m in enumerate(matches):
  for r in encoded:
   if when[r]==i:
    pair=(alloc(),alloc());decoded[r]=pair;body.extend(decode(r,*pair))
  for phase in [0,1]:
   step=2*i+phase
   for source,at in save_at.items():
    if at==step:
     tmp=alloc();saved[source]=tmp;body.append(f'mov.b32 {tmp}, {source};');backup_moves+=1
   def operand(r):
    if r not in mapped:return decoded[r][phase]
    source=mapped[r][phase];return saved.get(source,source)
   aa=[operand(m[n]) for n in ('a0','a1','a2','a3')];bb=[operand(m[n]) for n in ('b0','b1')];cc=[m['c0'],m['c1']] if phase==0 else [m['d0'],m['d1']]
   body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
   for source in list(saved):
    if last_read[source]==step:free.append(saved.pop(source))
  for r in list(decoded):
   if last[r]==i:free.extend(decoded.pop(r))
 decl=['{']
 if allocated:decl+=['.reg .b32 '+', '.join(f'vlh_t{i}' for i in range(allocated))+';']
 if encoded:decl+=['.reg .b32 dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale, 0x5c005c00;']
 if audit is not None:audit.append({'mma_sites':len(matches),'mapped_operands':sum(r in mapped for r in operands),'encoded_operands':len(encoded),'temporary_b32_peak':allocated,'backup_moves':backup_moves,'phase0_clobber_sources':sorted(save_at)})
 return '\n'.join(decl+body+['}'])

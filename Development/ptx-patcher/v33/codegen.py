"""Half-instruction DAG scheduling with frozen run-entry operand values."""
from ptx_mapped import mapped_at
from v26.codegen import render as legacy,decode
FIELDS=('a0','a1','a2','a3','b0','b1')
MODE='phase_pass'
ORIGINS={}
COUNTS={}
def render(matches,packed_sources,*,builder,audit=None):
 mapped=mapped_at(packed_sources,matches[0].start());operands=list(dict.fromkeys(m[n] for m in matches for n in FIELDS));encoded=[r for r in operands if r not in mapped]
 writes={m[n] for m in matches for n in ('d0','d1')}
 refs=set(encoded)|{s for r in operands if r in mapped for s in mapped[r][:2]}
 # Every operand read denotes a run-entry snapshot; raw snapshots permit late
 # decoding even when accumulator writes alias encoded/mapped original sources.
 clobbered=sorted(refs&writes);snap={s:f'vsnap{i}' for i,s in enumerate(clobbered)}
 instructions=[]
 for i,m in enumerate(matches):
  for ph in [0,1]:
   instructions.append((i,ph))
 if MODE=='phase_pass':
  levels=[];rw=[]
  for i,m in enumerate(matches):
   rd={m['c0'],m['c1']};wr={m['d0'],m['d1']}
   deps=[j for j,(r,w) in enumerate(rw) if w&(rd|wr) or wr&r]
   levels.append(1+max((levels[j] for j in deps),default=-1));rw.append((rd,wr))
  instructions=[(i,ph) for lev in range(max(levels)+1) for ph in [0,1] for i in range(len(matches)) if levels[i]==lev]
 else:levels=list(range(len(matches)))
 uses={}
 for step,(i,ph) in enumerate(instructions):
  for r in set(matches[i][n] for n in FIELDS):
   if r not in mapped:uses.setdefault((r,ph),[]).append(step)
 free=[];allocated=0;live={};body=[f'mov.b32 {dst}, {src};' for src,dst in snap.items()];decode_events=0;peak_live=0
 def alloc():
  nonlocal allocated
  if free:return free.pop()
  r=f'v33_t{allocated}';allocated+=1;return r
 for step,(i,ph) in enumerate(instructions):
  m=matches[i];needed=list(dict.fromkeys(m[n] for n in FIELDS));local={}
  for r in needed:
   if r in mapped:continue
   key=(r,ph)
   if MODE in ('remat','remat_call') or key not in live:
    dst=alloc();local[r]=dst;source=snap.get(r,r);selector=('0x9180','0xb3a2')[ph]
    if MODE=='remat_call':
     fn=('v33_decode_low','v33_decode_high')[ph]
     body+=['{','.param .b32 arg_in;','.param .b32 arg_out;',f'st.param.b32 [arg_in], {source};',f'call.uni (arg_out), {fn}, (arg_in);',f'ld.param.b32 {dst}, [arg_out];','}']
    else:body += [f'prmt.b32 {dst}, {source}, {source}, {selector};',f'and.b32 {dst}, {dst}, 0x017f017f;',f'shl.b32 {dst}, {dst}, 7;',f'mul.rn.f16x2 {dst}, {dst}, dlssnr_fp8_scale;']
    decode_events+=1
    if MODE not in ('remat','remat_call'):live[key]=dst
  peak_live=max(peak_live,len(live) if MODE not in ('remat','remat_call') else len(local))
  def operand(r):
   if r in mapped:return snap.get(mapped[r][ph],mapped[r][ph])
   return local[r] if MODE in ('remat','remat_call') else live[r,ph]
  a=[operand(m[n]) for n in FIELDS[:4]];b=[operand(m[n]) for n in FIELDS[4:]];c=[m['c0'],m['c1']] if ph==0 else [m['d0'],m['d1']]
  body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]},{m["d1"]}}}, {{{",".join(a)}}}, {{{",".join(b)}}}, {{{",".join(c)}}};')
  if MODE in ('remat','remat_call'):free.extend(local.values())
  else:
   for key in list(live):
    if uses[key][-1]==step:free.append(live.pop(key))
 decl=['{']
 if allocated:decl+=['.reg .b32 '+','.join(f'v33_t{i}' for i in range(allocated))+';']
 if snap:decl+=['.reg .b32 '+','.join(snap.values())+';']
 if encoded:decl+=['.reg .b32 dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']
 if audit is not None:
  audit.append({'mma_sites':len(matches),'mapped_operands':sum(r in mapped for r in operands),'encoded_operands':len(encoded),'temporary_b32_peak':allocated,'raw_snapshot_b32':len(snap),'backup_moves':len(snap),'decoded_half_events':decode_events,'original_decoded_half_events':2*len(encoded),'layer_count':max(levels)+1,'layer_sizes':[levels.count(l) for l in range(max(levels)+1)],'schedule':instructions,'mode':MODE})
 return '\n'.join(decl+body+['}'])

def render_probe(matches,packed_sources,*,builder,audit=None):
 # Preserve original v26 scheduling, backing, mapped eligibility, MMA and Pack;
 # only selected nonmapped operands become direct raw reads with no pool.
 text=matches[0].string;import re
 kernel=re.findall(r'\.visible \.entry (\w+)',text[:matches[0].start()])[-1]
 names={r for r in operands_of(matches) if r not in mapped_at(packed_sources,matches[0].start())}
 records=ORIGINS.get(kernel,{})
 groups=[];allms=list(builder.dp.FP8_MMA_PATTERN.finditer(text))
 for m in allms:
  if not groups or text[groups[-1][-1].end():m.start()].strip():groups.append([m])
  else:groups[-1].append(m)
 gi=next(i for i,g in enumerate(groups) if g[0].start()==matches[0].start())
 chosen={r for r in names if selected_leaf(records[(gi,r)]['leaf_categories'])}
 # Direct forwarding through fake mapped halves also preserves raw aliases by
 # old render's native-half overwrite backups. It intentionally destroys values.
 from ptx_mapped import Sources
 fake=Sources(packed_sources);fake.until=getattr(packed_sources,'until',{}).copy()
 for r in chosen:fake[r]=(r,r,-1);fake.until[r]=float('inf')
 local=[];out=legacy(matches,fake,builder=builder,audit=local)
 COUNTS.setdefault(kernel,{}).setdefault(MODE,0);COUNTS[kernel][MODE]+=len(chosen)
 if audit is not None:audit.extend(local)
 return out

def operands_of(matches):return list(dict.fromkeys(m[n] for m in matches for n in FIELDS))
def selected_leaf(leaves):
 leaves=set(leaves)
 if MODE=='probe_shared':return leaves=={'shared_load'}
 if MODE=='probe_global':return leaves=={'global_load'}
 if MODE=='probe_global_family':return 'global_load' in leaves
 if MODE=='probe_mixed':return 'global_load' in leaves and len(leaves)>1
 if MODE=='probe_both':return leaves in ({'shared_load'},{'global_load'})
 if MODE=='probe_all':return True
 raise ValueError(MODE)


def helper_functions():
 out=[]
 for name,selector in [('v33_decode_low','0x9180'),('v33_decode_high','0xb3a2')]:
  out += [f'.func (.param .b32 result) {name}(.param .b32 input_value)', '{','.reg .b32 x,k;','ld.param.b32 x,[input_value];',f'prmt.b32 x,x,x,{selector};','and.b32 x,x,0x017f017f;','shl.b32 x,x,7;','mov.b32 k,0x5c005c00;','mul.rn.f16x2 x,x,k;','st.param.b32 [result],x;','ret;','}']
 return '\n'.join(out)+'\n'

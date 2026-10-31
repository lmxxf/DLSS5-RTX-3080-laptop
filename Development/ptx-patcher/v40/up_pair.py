"""Direct 32-bit UP decode: explicit same-block reaching source and safe split DCE."""
import re,bisect,collections
from analysis_common import Origin,entries,REG,split_args,b
AUDIT=[]
def decode(src,dst,half):
 return [f'prmt.b32 {dst},{src},{src},{"0x9180" if half==0 else "0xb3a2"};',f'and.b32 {dst},{dst},0x017f017f;',f'shl.b32 {dst},{dst},7;','mov.b32 dlssnr_fp8_scale,0x5c005c00;',f'mul.rn.f16x2 {dst},{dst},dlssnr_fp8_scale;']
def analyze(part,cfg=False):
 o=Origin(part);rows=[];proof=__import__('cfg_proof').CFGProof(o) if cfg else None
 for m in b.dp.FP8_UP_PATTERN.finditer(part):
  point=bisect.bisect_right(o.starts,m.start())-1;defs=o.reach(m['source'],point);row={'line':part.count('\n',0,m.start())+1,'destination':m['destination'],'half_source':m['source'],'conversion_index':point,'eligible':False,'reason':'nonunique_definition'}
  if len(defs)==1:
   j,_=next(iter(defs));x=o.ins[j] if j>=0 else None
   if x and x['op']=='mov.b32' and x['argv'][0].startswith('{') and REG.fullmatch(x['argv'][1]):
    regs=REG.findall(x['argv'][0]);src=x['argv'][1];row.update(split_index=j,source32=src,half=regs.index(m['source']),split_halves=regs)
    if x['guard'] or m['guard']:row['reason']='guarded'
    elif o.owner[j]!=o.owner[point]:
     row['original_cross_block']=True
     if cfg:
      q=proof.prove(j,point,src);row['CFG_proof']=q;row.update(eligible=q['all_paths_unclobbered'],reason='CFG_unclobbered' if q['all_paths_unclobbered'] else 'CFG_clobbered_or_not_dominated')
     else:row['reason']='cross_block'
    elif any(src in t['writes'] for t in o.ins[j+1:point]):row['reason']='source_overwritten'
    else:row.update(eligible=True,reason='same_block_stable_unguarded')
   else:row['reason']='not_split32'
  rows.append(row)
 return o,rows
def lower(text,stats,fb,selected=None,cfg=False):
 parts=re.split(r'(?=\.visible \.entry )',text);count=0;deleted=0
 for i,part in enumerate(parts):
  if not part.startswith('.visible .entry '):continue
  n=re.match(r'\.visible \.entry (\w+)',part)[1];o,rows=analyze(part,cfg=cfg);changes=[];groups=collections.defaultdict(list);counts=collections.Counter(REG.findall(part))
  for r in rows:
   r.update(kernel=n,FB=fb,applied=r['eligible'] and (selected is None or n in selected));AUDIT.append(r)
   if not r['applied']:continue
   x=o.ins[r['conversion_index']];changes.append((x['start'],x['end'],'\n'.join(['{','.reg .b32 dlssnr_fp8_scale;']+decode(r['source32'],r['destination'],r['half'])+['}'])));groups[r['split_index']].append(r);count+=1
  for j,rs in groups.items():
   regs=rs[0]['split_halves'];remove=len(rs)==2 and {r['half'] for r in rs}=={0,1} and all(counts[r]==2 for r in regs)
   for r in rs:r['split_deleted']=remove
   if remove:x=o.ins[j];changes.append((x['start'],x['end'],''));deleted+=1
  for a,z,new in sorted(changes,reverse=True):part=part[:a]+new+part[z:]
  parts[i]=part
 stats.add('fp8_to_fp16',count);stats.add('up_pair_deleted_splits',deleted);return ''.join(parts)

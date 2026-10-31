from pathlib import Path
import json,re,bisect,collections
from analysis_common import Origin,entries
p=Path(__file__).resolve().parent;old=json.loads((p.parent/'v27/source-audit.json').read_text());rows=[]
for fb in range(7):
 text=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text()
 for name,entry in entries(text):
  if name not in old['fatbins'][str(fb)]:continue
  target=[r for r in old['fatbins'][str(fb)][name]['records'] if r['reason']=='pack_multidef']
  if not target:continue
  o=Origin(entry);from analysis_common import b
  ms=list(b.dp.FP8_MMA_PATTERN.finditer(entry));groups=[]
  for m in ms:
   if not groups or entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  for r in target:
   point=bisect.bisect_right(o.starts,groups[r['run']][0].start())-1;defs=o.reach(r['register'],point);proof=[]
   for j,s in sorted(defs):
    x=o.ins[j] if j>=0 else None;bid=o.owner[j] if j>=0 else None
    proof.append({'index':j,'line':entry.count('\n',0,x['start'])+1 if x else None,'register':s,'text':x['text'] if x else 'undefined','guard':x['guard'] if x else None,'root_kind':o.root_kind((j,s)),'block':bid,'predecessors':sorted(o.preds[bid]) if bid is not None else [],'predecessor_terminators':[{ 'block':q,'tail':[i['text'] for i in o.blocks[q]['ins'][-3:]]} for q in sorted(o.preds[bid])] if bid is not None else []})
   rows.append({'FB':fb,'kernel':name,'register':r['register'],'run':r['run'],'consumer_line':entry.count('\n',0,o.ins[point]['start'])+1,'consumer_text':o.ins[point]['text'],'consumer_block':o.owner[point],'reaching_definition_count':len(defs),'leaf_categories':sorted(o.leaves(defs)),'definitions':proof,'unique_pack_definition':len(defs)==1 and all(o.root_kind(d)=='mov.pack16' for d in defs),'decision':'multiple possible definitions; cannot unconditionally replace memory-path data with fallback native half' if len(defs)>1 else 'requires quantization/source-stability proof'})
assert len(rows)==36
out={'scope':'36 static rejected run/register events, original PTX entry-relative line numbers; CFG may-reaching definitions','event_count':len(rows),'unique_pack_events':sum(r['unique_pack_definition'] for r in rows),'definition_count_histogram':dict(collections.Counter(r['reaching_definition_count'] for r in rows)),'records':rows}
(p/'multidef36-audit.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='records'})

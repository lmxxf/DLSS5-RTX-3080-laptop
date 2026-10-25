#!/usr/bin/env python3
"""Static PTX memory-op census; distinguishes scalar bytes from word vectors."""
from pathlib import Path
from collections import Counter
import re,json,argparse
root=Path(__file__).resolve().parents[1]
def count(text):
 ops=Counter();summary=Counter()
 for m in re.finditer(r'\b(?:ld|st)(?:\.[A-Za-z0-9_:]+)+',text):
  op=m[0];parts=op.split('.');space=next((x for x in ('global','shared') if x in parts),None)
  if space is None:continue
  ops[op]+=1;prefix=parts[0]+'_'+space
  vector=next((x for x in ('v2','v4') if x in parts),None)
  if parts[-1]=='u8' and vector is None:summary[prefix+'_u8']+=1
  if vector and parts[-1] in ('u32','b32','f32'):summary[prefix+'_'+vector+'_32']+=1
  elif vector:summary[prefix+'_vector_other']+=1
 return {'summary':dict(summary),'opcodes':dict(sorted(ops.items()))}

def main():
    p=argparse.ArgumentParser();p.add_argument('--modules',type=Path,default=root/'phase6/artifacts/aligned16/modules');a=p.parse_args()
    rows={}
    for binary in sorted(a.modules.glob('*.hsaco')):
        file=binary.with_suffix('.ptx')
        if not file.exists():file=root/'phase6/artifacts/aligned16/modules'/file.name
        old=root/'phase5/artifacts/selected/modules'/file.name
        if not old.exists():old=root/'phase5/artifacts/vector/modules'/file.name
        if not old.exists():continue
        rows[file.stem]={'baseline_path':str(old),'baseline':count(old.read_text()),'aligned':count(file.read_text())}
    assert len(rows)==40,len(rows)
    report=['# PTX memory instruction census','', 'Static counts include all entry points and helpers, not per-frame dynamic execution. Word vectors are v2/v4 of 32-bit elements.','', '| Module | Scalar u8 before→after | Word v2 before→after | Word v4 before→after |','|---|---:|---:|---:|']
    for name,r in rows.items():
     vals=[]
     for suffix in ('_u8','_v2_32','_v4_32'):
      vals.append('→'.join(str(sum(v for k,v in r[x]['summary'].items() if k.endswith(suffix))) for x in ('baseline','aligned')))
     report.append('| '+name+' | '+' | '.join(vals)+' |')
    (root/'phase6/ptx-counts.json').write_text(json.dumps(rows,indent=2)+'\n');(root/'phase6/ptx-counts.md').write_text('\n'.join(report)+'\n')
    print('\n'.join(report[:11]))

if __name__=="__main__":main()

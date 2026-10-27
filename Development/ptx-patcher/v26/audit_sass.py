from pathlib import Path
import json,re,collections,subprocess
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';result={'baseline':json.loads((p.parent/'v24/sass-audit.json').read_text())['c']};active=set(result['baseline'])
for tag in ['decode']:
 result[tag]={}
 for fb in range(7):
  sass=subprocess.check_output([tool,'-sass',str(p/f'artifacts/{tag}/fatbin{fb:02d}.cubin')],text=True,stderr=subprocess.DEVNULL)
  for ch in sass.split('Function : ')[1:]:
   name=ch.splitlines()[0].strip()
   if name not in active:continue
   ops=collections.Counter(re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?[UP]+\d+\s+)?([A-Z][A-Z0-9_.]+)',ch));family=collections.Counter()
   for op,n in ops.items():family[op.split('.')[0]]+=n
   result[tag][name]={'FB':fb,'static_SASS_instructions':sum(ops.values()),'full_opcodes':dict(ops),'families':dict(family)}
 for n,r in result['baseline'].items():
  if r['FB']>6:result[tag][n]=r
 for n in active:assert result[tag][n]['families'].get('HMMA',0)==result['baseline'][n]['families'].get('HMMA',0)
 print(tag,sum(x['static_SASS_instructions'] for x in result[tag].values()),flush=True)
(p/'sass-audit.json').write_text(json.dumps(result,indent=2)+'\n')

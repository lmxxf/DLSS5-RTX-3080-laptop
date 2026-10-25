#!/usr/bin/env python3
from pathlib import Path
import re,json,importlib.util,sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from count_ptx import count
rows=[]
for module,kernel in [('c64-wave2-fast','c64_wave2_bi_bo_w16'),('c64-wave2-fast','c128_wave2_bi_bo_w16'),('c64-wave2-fast','c256_wave2_bi_bo_w16'),('c32-wave1-fast','c32_wave1_prefix_b8d_w16')]:
 row={'module':module,'kernel':kernel}
 for label,folder in [('baseline',root/'phase5/artifacts/selected/modules'),('aligned',root/'phase6/artifacts/aligned16/modules')]:
  p=folder/(module+'.ptx')
  if not p.exists():p=root/'phase5/artifacts/vector/modules'/(module+'.ptx')
  text=p.read_text();m=re.search(r'\.visible\s+\.entry\s+'+re.escape(kernel)+r'\(',text);assert m
  a=text.index('{',m.end());n=1;e=a+1
  while n:n+=(text[e]=='{')-(text[e]=='}');e+=1
  b=text[a:e];row[label]={'lines':len(b.splitlines()),**count(b)}
 rows.append(row)
(root/'phase6/hot-kernel-ptx.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(r['kernel'],r['baseline']['lines'],r['aligned']['lines'],r['baseline']['summary'],r['aligned']['summary'])

#!/usr/bin/env python3
from pathlib import Path
import re,json
root=Path(__file__).resolve().parent

def body(text,name):
 m=re.search(r'\.visible\s+\.entry\s+'+name+r'\(',text);assert m,name
 a=text.index('{',m.end());e=a+1;n=1
 while n:n+=(text[e]=='{')-(text[e]=='}');e+=1
 return text[a:e]
def counts(t):
 return {k:len(re.findall(p,t)) for k,p in {'bra':r'\bbra(?:\.uni)?\s','min':r'\bmin\.[\w.]+\s','max':r'\bmax\.[\w.]+\s','mma':r'\bmma\.sync\.', 'lines':r'\n'}.items()}
rows=[]
for module,kernel in [('c32-wave1-fast','c32_wave1_prefix_b8d_w16'),('c32-wave1-fast','c32_wave1_mapped_b8_w16'),('c64-wave2-fast','c64_wave2_bi_bo_w16'),('c64-wave2-fast','c128_wave2_bi_bo_w16'),('c64-wave2-fast','c256_wave2_bi_bo_w16')]:
 row={'module':module,'kernel':kernel}
 for label,folder in [('baseline',root.parent/'phase6/artifacts/selected/modules'),('step12',root/'artifacts/step12/modules'),('hoist',root/'artifacts/hoist/modules')]:
  p=folder/(module+'.ptx')
  if not p.exists():p=root.parent/'phase6/artifacts/aligned16/modules'/(module+'.ptx') if label=='baseline' else root/'artifacts/step12/modules'/(module+'.ptx')
  if p.exists():row[label]=counts(body(p.read_text(),kernel))
 rows.append(row)
(root/'ptx-counts.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Static PTX instructions per entry','', 'These are static PTX counts, not executed instruction counts or final SASS. Hoist uses step12 for unchanged non-C32 modules.','', '| Kernel | Variant | bra | min | max | mma | Lines |','|---|---|---:|---:|---:|---:|---:|']
for r in rows:
 for v in ('baseline','step12','hoist'):
  if v in r:lines.append('| '+r['kernel']+' | '+v+' | '+' | '.join(str(r[v][k]) for k in ('bra','min','max','mma','lines'))+' |')
(root/'ptx-counts.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
module_rows=[]
for p in sorted((root/'artifacts/step12/modules').glob('*.ptx')):
 before=root.parent/'phase6/artifacts/selected/modules'/p.name
 if not before.exists():before=root.parent/'phase6/artifacts/aligned16/modules'/p.name
 assert before.exists(),p.name
 module_rows.append({'module':p.stem,'baseline':counts(before.read_text()),'step12':counts(p.read_text())})
(root/'ptx-module-counts.json').write_text(json.dumps(module_rows,indent=2)+'\n')
lines=['# Static PTX module totals (including unused entry points)','', '| Module | bra before→after | min before→after | max before→after |','|---|---:|---:|---:|']
for r in module_rows:lines.append('| '+r['module']+' | '+' | '.join(f'{r["baseline"][k]}→{r["step12"][k]}' for k in ('bra','min','max'))+' |')
(root/'ptx-module-counts.md').write_text('\n'.join(lines)+'\n')

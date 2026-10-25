from pathlib import Path
import re,json
root=Path(__file__).resolve().parent

def body(t,k):
 m=re.search(r'\.visible\s+\.entry\s+'+k+r'\(',t);assert m,k
 a=t.index('{',m.end());e=a+1;n=1
 while n:n+=(t[e]=='{')-(t[e]=='}');e+=1
 return t[a:e]
def counts(t):
 out={k:len(re.findall(p,t)) for k,p in {'min':r'\bmin\.[\w.]+\s','max':r'\bmax\.[\w.]+\s','setp':r'\bsetp\.[\w.]+\s','selp':r'\bselp\.[\w.]+\s','bra':r'\bbra(?:\.uni)?\s','mma':r'\bmma\.sync\.', 'shfl':r'\bshfl\.sync\.'}.items()}
 return out
rows=[]
for mod,kernel in [('c32-wave1-fast','c32_wave1_prefix_b8d_w16'),('c32-wave1-fast','c32_wave1_mapped_b8_w16'),('c32-wave1-fast','c32_wave1_up_b8_w16'),('c64-wave2-fast','c64_wave2_bi_bo_w16'),('c64-wave2-fast','c128_wave2_bi_bo_w16'),('c64-wave2-fast','c256_wave2_bi_bo_w16'),('c512-m32-mh','c512_qkv_attention_compact_w16')]:
 r={'module':mod,'kernel':kernel}
 for v,folder in [('phase9',root.parent/'phase9/artifacts/selected/modules'),('caps',root/'artifacts/caps/modules'),('selected',root/'artifacts/selected/modules')]:
  p=folder/(mod+'.ptx')
  if not p.exists():p=root.parent/'phase9/artifacts/selected/modules'/(mod+'.ptx')
  r[v]=counts(body(p.read_text(),kernel))
 rows.append(r)
(root/'ptx-counts.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Phase 10 static PTX per entry','', 'Counts are static PTX, not executed SASS. Saturation moved into the converter can increase min count when a wrapper already had no outer clamp.','', '| Kernel | min | max | setp | selp | bra | mma | shfl |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append('| '+r['kernel']+' | '+' | '.join(f'{r["phase9"][k]}→{r["selected"][k]}' for k in ['min','max','setp','selp','bra','mma','shfl'])+' |')
(root/'ptx-counts.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

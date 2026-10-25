from pathlib import Path
import re,json
root=Path(__file__).resolve().parent

def body(t,k):
 m=re.search(r'\.visible\s+\.entry\s+'+k+r'\(',t);assert m,k
 a=t.index('{',m.end());e=a+1;n=1
 while n:n+=(t[e]=='{')-(t[e]=='}');e+=1
 return t[a:e]
def count(t):return {k:len(re.findall(p,t)) for k,p in {'shfl':r'\bshfl\.sync\.', 'selp':r'\bselp\.', 'prmt':r'\bprmt\.b32\s','mma':r'\bmma\.sync\.', 'bra':r'\bbra(?:\.uni)?\s','lines':r'\n'}.items()}
rows=[]
for module,kernel in [('c32-wave1-fast','c32_wave1_prefix_b8d_w16'),('c32-wave1-fast','c32_wave1_mapped_b8_w16'),('c32-wave1-fast','c32_wave1_post_b8_w16'),('c64-wave2-fast','c64_wave2_bi_bo_w16'),('c64-wave2-fast','c128_wave2_bi_bo_w16'),('c64-wave2-fast','c256_wave2_bi_bo_w16')]:
 row={'module':module,'kernel':kernel}
 for label,folder in [('baseline',root.parent/'phase7/artifacts/selected/modules'),('full',root/'artifacts/full/modules'),('selected',root/'artifacts/selected/modules')]:row[label]=count(body((folder/(module+'.ptx')).read_text(),kernel))
 rows.append(row)
(root/'ptx-counts.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Phase 8 static PTX per active entry','', 'Static PTX counts do not measure dynamic execution or final SASS.','', '| Kernel | shfl | selp | prmt | mma | bra | PTX lines |','|---|---:|---:|---:|---:|---:|---:|']
for r in rows:
 for v in ['full','selected']:lines.append('| '+r['kernel']+' ('+v+') | '+' | '.join(f'{r["baseline"][k]}→{r[v][k]}' for k in ('shfl','selp','prmt','mma','bra','lines'))+' |')
(root/'ptx-counts.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

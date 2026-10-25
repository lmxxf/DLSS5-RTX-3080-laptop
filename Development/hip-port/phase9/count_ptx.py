from pathlib import Path
import re,json
root=Path(__file__).resolve().parent

def body(t,k):
 m=re.search(r'\.visible\s+\.entry\s+'+k+r'\(',t);assert m,k
 a=t.index('{',m.end());e=a+1;n=1
 while n:n+=(t[e]=='{')-(t[e]=='}');e+=1
 return t[a:e]
def counts(t):return {k:len(re.findall(p,t)) for k,p in {'shfl':r'\bshfl\.sync\.', 'selp':r'\bselp\.', 'prmt':r'\bprmt\.b32\s','bra':r'\bbra(?:\.uni)?\s','mma':r'\bmma\.sync\.', 'lines':r'\n'}.items()}
rows=[]
for mod,kernel in [('c32-wave1-fast','c32_wave1_prefix_b8d_w16'),('c32-wave1-fast','c32_wave1_mapped_b8_w16'),('c32-wave1-fast','c32_wave1_finish_b8_w16'),('c64-wave2-fast','c64_wave2_bi_bo_w16'),('c64-wave2-fast','c128_wave2_bi_bo_w16'),('c64-wave2-fast','c256_wave2_bi_bo_w16')]:
 row={'module':mod,'kernel':kernel}
 for name,folder in [('phase8',root.parent/'phase8/artifacts/selected/modules'),('v-bridge',root/'artifacts/v-bridge/modules'),('selected',root/'artifacts/selected/modules')]:row[name]=counts(body((folder/(mod+'.ptx')).read_text(),kernel))
 rows.append(row)
(root/'ptx-counts.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Phase 9 static PTX per entry','', 'Counts include loops statically; do not treat them as dynamic instructions or SASS.','', '| Kernel | Variant | shfl | selp | prmt | bra | mma |','|---|---|---:|---:|---:|---:|---:|']
for r in rows:
 for v in ['phase8','v-bridge','selected']:lines.append('| '+r['kernel']+' | '+v+' | '+' | '.join(str(r[v][k]) for k in ['shfl','selp','prmt','bra','mma'])+' |')
(root/'ptx-counts.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

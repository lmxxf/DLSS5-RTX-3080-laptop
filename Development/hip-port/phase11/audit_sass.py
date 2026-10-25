from pathlib import Path
import re,json,subprocess
root=Path(__file__).resolve().parent
paths={'phase10':root/'artifacts/audit/phase10-c32.sass','half-store':root/'artifacts/audit/half-store-c32.sass','half-feature-pack':root/'artifacts/audit/half-feature-pack-c32.sass'}
rows=[]
for kernel in ['c32_wave1_prefix_b8d_w16','c32_wave1_post_b8_w16','c32_wave1_mapped_b8_w16']:
 row={'kernel':kernel}
 for v,p in paths.items():
  if not p.exists():
   binary=(root.parent/'phase10/artifacts/selected/modules' if v=='phase10' else root/'artifacts'/v/'modules')/'c32-wave1-fast.hsaco'
   with p.open('w') as out:subprocess.run(['/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump','--dump-sass',str(binary)],stdout=out,check=True)
  s=p.read_text();a=s.index('Function : '+kernel);z=s.find('Function : ',a+12);s=s[a:z if z>=0 else None]
  count={}
  for line in s.splitlines():
   m=re.search(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)\b',line)
   if m:count[m[1]]=count.get(m[1],0)+1
  row[v]={'instruction_slots':sum(count.values()),'opcodes':count}
 rows.append(row)
(root/'sass-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:
 print(r['kernel'])
 for v,c in r.items():
  if v=='kernel':continue
  print(v,c['instruction_slots'],{k:n for k,n in c['opcodes'].items() if k.startswith(('F2F','HMNMX','HADD','HMMA','SHFL','LDL','STL'))})

from pathlib import Path
import subprocess,json,re
root=Path(__file__).resolve().parents[1];phase=root/'phase12';tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
sets=[('baseline-c32',root/'phase11/artifacts/selected/modules/c32-wave1-fast.hsaco',['c32_wave1_prefix_b8d_w16','c32_wave1_post_b8_w16']),('baseline-wave2',root/'phase11/artifacts/selected/modules/c64-wave2-fast.hsaco',['c64_wave2_bi_bo_w16','c128_wave2_bi_bo_w16','c256_wave2_bi_bo_w16'])]
for site in ['c32-av','c32-v','wave2-av','wave2-v']:
 mod='c32-wave1-fast' if site.startswith('c32') else 'c64-wave2-fast';kernels=sets[0 if site.startswith('c32') else 1][2];sets.append((site,phase/'artifacts'/site/'modules'/(mod+'.hsaco'),kernels))
rows={}
for label,binary,kernels in sets:
 out=phase/'artifacts/sass'/(label+'.sass')
 if not out.exists():
  with out.open('w') as f:subprocess.run([tool,'--dump-sass','--function',','.join(kernels),str(binary)],stdout=f,check=True)
 text=out.read_text();rows[label]={}
 for k in kernels:
  m=text.find('Function : '+k)
  if m<0:continue
  end=text.find('Function : ',m+12);s=text[m:end if end>=0 else None];ops={}
  for line in s.splitlines():
   op=re.search(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)\b',line)
   if op:ops[op[1]]=ops.get(op[1],0)+1
  rows[label][k]={'slots':sum(ops.values()),'opcodes':ops}
(phase/'sass-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
for label,row in rows.items():print(label,{k:v['slots'] for k,v in row.items()})

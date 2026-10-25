from pathlib import Path
import subprocess,re,json
r=Path(__file__).resolve().parents[1];p=r/'phase13';folder=p/'artifacts/sass';folder.mkdir(exist_ok=True);tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
rows={}
for variant,kind in [('baseline','prefix'),('baseline','post'),('prefix','prefix'),('post','post')]:
 name='c32_wave1_prefix_b8d_w16' if kind=='prefix' else 'c32_wave1_post_b8_w16';mod=r/'phase12/artifacts/selected/modules/c32-wave1-fast.hsaco' if variant=='baseline' else p/f'artifacts/{variant}/modules/c32-wave1-fast.hsaco';out=folder/f'{variant}-{kind}.sass'
 with out.open('w') as f:subprocess.run([tool,'--dump-sass','--function',name,str(mod)],stdout=f,stderr=subprocess.DEVNULL,check=True)
 txt=out.read_text();m=txt.index('Function : '+name);end=txt.find('Function : ',m+12);txt=txt[m:end if end>=0 else None]
 inst=[]
 for line in txt.splitlines():
  match=re.search(r'/\*([0-9a-f]+)\*/\s+(.+?);',line)
  if match:inst.append((int(match[1],16),match[2]))
 mma=[]
 for i,(addr,line) in enumerate(inst):
  if 'HMMA.' in line:
   regs=re.findall(r'\bR\d+\b',line);mma.append({'pc':hex(addr),'instruction':line,'previous_4':[x[1] for x in inst[max(i-4,0):i]],'next_4':[x[1] for x in inst[i+1:i+5]]})
 # Preserve real producer/consumer registers and nearby load/convert instructions.
 rows[f'{variant}-{kind}']={'entry':name,'static_sass_slots':len(inst),'HMMA_sites':mma,'caveat':'Static register def/use witnesses support the sampled execution path, not hardware stall metrics or speed estimates.'}
(p/'dependency-witnesses.json').write_text(json.dumps(rows,indent=2)+'\n');print({k:(v['static_sass_slots'],len(v['HMMA_sites'])) for k,v in rows.items()})

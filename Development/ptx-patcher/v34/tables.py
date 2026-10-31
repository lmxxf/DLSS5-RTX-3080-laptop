from pathlib import Path
import json,re,math,hashlib
p=Path(__file__).resolve().parent;data=json.loads((p/'resources.json').read_text());dynamic=json.loads((p.parent/'v25/dynamic-ledger.json').read_text());loops=json.loads((p.parent/'v25/natural-loops.json').read_text());out=[];sync={}
for mode,rows in data.items():
 lines=[f'# {mode}: four hardware tables','','Static counts cover exactly 38 launched FP8 entries. Loop observations below are inherited V2.5 semantic-loop instrumentation, not newly measured hardware-issued counts. Grid/block from V2.3 real NVAPI launches (dynamic shared=0). Occupancy is freshly queried from each actual cubin. No NCU counters are available in this experiment.','', '## 1. Instructions and loop evidence','','|Kernel|nonNOP|HMMA|PRMT|SHF|LOP3|Historical compute loop visits/warp (720p)|','|---|---:|---:|---:|---:|---:|---|']
 for n,r in rows.items():
  hist=dynamic['1280']['kernels'].get(n,{})
  desc=','.join(str(q['mean_iterations_per_launched_warp']) for q in hist.get('loops',[])) or ('unrolled / no compute loop' if not loops.get(n,{}).get('loops') else 'not dynamically captured')
  lines.append('|'+n+'|'+'|'.join(str(r[k]) for k in ['INSN_NONOP','HMMA','PRMT','SHF','LOP3'])+'|'+desc+'|')
 lines+=['','## 2. Registers and local memory','','|Kernel|REG|STACK B|LOCAL B|STL|LDL|','|---|---:|---:|---:|---:|---:|']
 for n,r in rows.items():lines.append('|'+n+'|'+'|'.join(str(r.get(k,0)) for k in ['REG','STACK','LOCAL','STL','LDL'])+'|')
 lines+=['','## 3. Official resident limit and finite grid','','Waves = ceil(grid CTAs / (48 SM * theoretical resident CTAs)); this is capacity arithmetic, not measured concurrency. Multiple calls may use different grids; raw launch source remains v23/profile.json.','','|Kernel|Threads|CTA/SM|Warps/SM|720 grid|720 capacity waves|1080 grid|1080 capacity waves|','|---|---:|---:|---:|---|---:|---|---:|']
 for n,r in rows.items():
  grids=[r['grids'][w] for w in ['1280','1920']];v=[]
  for g in grids:v += [str(g),str(math.ceil(math.prod(g)/(48*r['resident_CTA_per_SM']))) if g else 'NA']
  lines.append('|'+n+'|'+'|'.join(map(str,[r['threads'],r['resident_CTA_per_SM'],r['resident_warps_per_SM']]+v))+'|')
 lines+=['','## 4. Shuffle and async wait distance','','Distances count lexical PTX statements from cp.async to next arrive/test_wait, and can cross control flow. They are NOT CFG shortest paths, runtime overlaps, stall counters, or a latency budget. Async completion rewrite is unchanged from the independently audited V2.2 mbarrier path.','','|Kernel|SASS SHFL|SASS LDGSTS|PTX async-to-next-wait lexical distance range|','|---|---:|---:|---|']
 for n,r in rows.items():
  f=p/f'artifacts/{mode}/fatbin{r["FB"]:02}.ptx';text=f.read_text();match=re.search(r'\.visible \.entry '+re.escape(n)+r'\b',text);tail=text[match.end():];nextentry=re.search(r'\.visible \.entry ',tail);tail=tail[:nextentry.start()] if nextentry else tail
  statements=tail.split(';');copies=[i for i,s in enumerate(statements) if 'cp.async.' in s];waits=[i for i,s in enumerate(statements) if any(x in s for x in ['mbarrier.arrive','mbarrier.test_wait','cp.async.wait_group'])];dist=[min(w-i for w in waits if w>i) for i in copies if any(w>i for w in waits)];sync[mode,n]={'copy_sites':len(copies),'lexical_distances':dist}
  lines.append(f'|{n}|{r["SHFL"]}|{r["LDGSTS"]}|{str((min(dist),max(dist))) if dist else "none"}|')
 (p/f'hardware-{mode}.md').write_text('\n'.join(lines)+'\n')
print('tables',len(data))

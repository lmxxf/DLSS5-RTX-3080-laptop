"""CFG-aware original-PTX audit; follow loop backedges to next arrive."""
from pathlib import Path
import re,json,collections
p=Path(__file__).resolve().parent;result={}
for fb in [4,5,6]:
 s=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text();rows=[]
 for entry in re.split(r'(?=\.visible \.entry )',s)[1:]:
  lines=entry.splitlines();labels={l.strip()[:-1]:i for i,l in enumerate(lines) if re.fullmatch(r'\s*\$[\w_]+:\s*',l)}
  for start,l in enumerate(lines):
   if not l.startswith('cp.async.bulk.'):continue
   # shortest control-flow paths; branches retain both successors unless bra.uni.
   q=collections.deque([(start+1,0)]);seen=set();found=[];exits=0
   while q:
    at,n=q.popleft()
    if at in seen:continue
    seen.add(at)
    if at>=len(lines):exits+=1;continue
    line=lines[at].strip()
    if line.startswith('mbarrier.arrive.'):
     found.append({'instruction_distance':n,'arrive_entry_line':at+1});continue
    if line=='ret;':exits+=1;continue
    b=re.search(r'\bbra(?:\.uni)?\s+(\$[\w_]+);',line)
    if b:
     q.append((labels[b[1]],n+1))
     if not line.startswith('@'):continue
    q.append((at+1,n+int(';' in line)))
   rows.append({'entry':entry.splitlines()[0],'copy_entry_line':start+1,'next_arrivals':found,'possible_exits_before_next_arrive':exits})
 ds=[a['instruction_distance'] for r in rows for a in r['next_arrivals']]
 result[str(fb)]={'copy_sites':len(rows),'min_max_CFG_instructions_to_next_arrive':[min(ds),max(ds)],'copy_sites_with_exit_paths':sum(bool(r['possible_exits_before_next_arrive']) for r in rows),'rows':rows}
result['semantics']={'init':'ntid.x * ntid.y; both alternating buffers','original_arrive_count':1,'new_async_arrival':'cp.async.mbarrier.arrive.shared::cta.b64 (increment enabled)','reason':'Per issuing lane increments pending count, then completion decrements it; original CTA arrivals unchanged. noinc would consume original participant arrivals and is incorrect without changing init.','source':'https://docs.nvidia.com/cuda/archive/12.0.1/parallel-thread-execution/index.html#parallel-synchronization-and-communication-instructions-cp-async-mbarrier-arrive'}
(p/'async-audit.json').write_text(json.dumps(result,indent=2)+'\n');print({k:{a:b for a,b in v.items() if a!='rows'} for k,v in result.items() if k!='semantics'})

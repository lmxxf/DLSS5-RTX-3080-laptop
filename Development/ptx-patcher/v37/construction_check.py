from pathlib import Path
import json,hashlib,collections
from unrolled import refresh_code,QKV
p=Path(__file__).resolve().parent;res=json.loads((p/'resources.json').read_text());cs=json.loads((p/'candidates.json').read_text());plan=json.loads((p/'async-plans.json').read_text())[QKV];prof=json.loads((p.parent/'v23/profile.json').read_text());blocks={tuple(x['block']) for r in prof.values() for x in r['calls'] if x['name']==QKV};assert len(blocks)==1;nx,ny,nz=next(iter(blocks));seen=[]
for tz in range(nz):
 for ty in range(ny):
  for tx in range(nx):
   tid=(tz*ny+ty)*nx+tx
   seen.extend(tid*4+offset for offset in range(0,8192,128*4))
assert sorted(seen)==list(range(0,8192,4))
code=refresh_code(plan,0);assert 'bra ' not in code and '%ntid' not in code and 'setp.' not in code
out={'baseline_sha256':cs['baseline']['sha256'],'actual_block':list(next(iter(blocks))),'refresh_points':plan['refresh_points'],'unrolled_words_per_thread':16,'all_2048_words_exactly_once':True,'branch_free_refresh':True,'dynamic_ntid_uses_in_refresh':0,'static_resource_deltas':{}}
for mode in cs:
 out['static_resource_deltas'][mode]={n:{k:[res['baseline'][n][k],r[k]] for k in ['REG','STACK','STL','LDL','INSN_NONOP','PRMT','SHARED','resident_CTA_per_SM'] if r[k]!=res['baseline'][n][k]} for n,r in res[mode].items() if r!=res['baseline'][n]}
# Candidate source identity and unchanged-entry checks are independently in preflight.
(p/'construction-validation.json').write_text(json.dumps(out,indent=2)+'\n');print('coverage PASS; qkv resources', {n:{k:res[n][QKV][k] for k in ['REG','STACK','STL','LDL','INSN_NONOP','resident_CTA_per_SM']} for n in ['baseline','async_qkv_only','async_qkv_unrolled']})

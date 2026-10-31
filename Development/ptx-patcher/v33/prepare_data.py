"""Build objective source/machine tables before narrative or timed selection."""
from pathlib import Path
import json,hashlib,struct,subprocess,re
p=Path(__file__).resolve().parent;res=json.loads((p/'resources.json').read_text());candidates=json.loads((p/'candidates.json').read_text());active=res['baseline'];summaries={};probe_counts={}
for mode in candidates:
 by_kernel={n:{'temporary_b32_peak':0,'raw_snapshot_b32_peak':0,'decoded_half_events':0,'original_decoded_half_events':0,'runs':0} for n in active};counts={}
 for f in sorted(p.glob(f'pool-{mode}-fb*.json')):
  d=json.loads(f.read_text())
  for r in d['runs']:
   if 'schedule' in r:r['schedule_sha256']=hashlib.sha256(json.dumps(r.pop('schedule')).encode()).hexdigest()
   n=r['kernel']
   if n not in active:continue
   q=by_kernel[n];q['temporary_b32_peak']=max(q['temporary_b32_peak'],r['temporary_b32_peak']);q['raw_snapshot_b32_peak']=max(q['raw_snapshot_b32_peak'],r.get('raw_snapshot_b32',0));q['decoded_half_events']+=r.get('decoded_half_events',2*r['encoded_operands']);q['original_decoded_half_events']+=r.get('original_decoded_half_events',2*r['encoded_operands']);q['runs']+=1
  f.write_text(json.dumps(d,indent=2)+'\n')
  for n,values in d['probe_events'].items():
   for tag,v in values.items():counts[n]=counts.get(n,0)+v
 summaries[mode]=by_kernel
 if mode.startswith('probe_'):probe_counts[mode]={'events':sum(counts.values()),'by_kernel':counts}
assert {n:r['events'] for n,r in probe_counts.items()}=={'probe_shared':2320,'probe_global':3304,'probe_mixed':224,'probe_both':5624,'probe_all':5848,'probe_global_family':3528}
assert all(r['decoded_half_events']==r['original_decoded_half_events'] for r in summaries['phase_pass'].values())
(p/'source-summary.json').write_text(json.dumps(summaries,indent=2)+'\n');(p/'probe-events.json').write_text(json.dumps(probe_counts,indent=2)+'\n')
lines=['# V3.3 source temporary pool peaks','','Each cell is the max virtual b32 decoder pool per MMA run, not total physical registers. Raw snapshots are counted separately. Phase-pass exactly preserves total half-decode events.','','|Kernel|Baseline|Phase-pass|Remat spill|Phase guarded|','|---|---:|---:|---:|---:|']
for n in active:lines.append('|'+n+'|'+'|'.join(str(summaries[m][n]['temporary_b32_peak']) for m in ['baseline','phase_pass','remat_spill','phase_guarded'])+'|')
(p/'pool-summary.md').write_text('\n'.join(lines)+'\n')
def sections(f):
 d=f.read_bytes();off=struct.unpack_from('<Q',d,40)[0];size,num,strings=struct.unpack_from('<HHH',d,58);hs=[struct.unpack_from('<IIQQQQIIQQ',d,off+i*size) for i in range(num)];st=hs[strings];names=d[st[4]:st[4]+st[5]]
 return {names[h[0]:].split(b'\0')[0].decode()[6:]:d[h[4]:h[4]+h[5]] for h in hs if names[h[0]:].split(b'\0')[0].startswith(b'.text.')}
identity={}
for mode in candidates:
 diffs=[];whole=[];ks={}
 for fb in range(15):
  a=p/f'artifacts/{mode}/fatbin{fb:02}.cubin';b=p/f'artifacts/baseline/fatbin{fb:02}.cubin';same=a.read_bytes()==b.read_bytes();whole.append(same)
  if fb<7:
   aa,bb=sections(a),sections(b)
   for n,r in active.items():
    if r['FB']==fb:ks[n]=aa[n]==bb[n]
 identity[mode]={'whole_cubin_equal_to_baseline':whole,'active_text_identical':all(ks.values()),'active_text_equal_by_kernel':ks}
 if mode=='quad_fb23':assert all(whole[i] for i in range(15) if i not in (2,3))
 if mode=='remat_fb1':assert all(whole[i] for i in range(15) if i!=1)
 if mode=='remat_qkv':assert all(whole[i] for i in range(15) if i!=4)
(p/'machine-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';helpers=[]
for fb in (1,4):
 text=subprocess.check_output([tool,'-sass',str(p/f'artifacts/remat_call/fatbin{fb:02}.cubin')],text=True)
 for part in re.split(r'Function : ',text)[1:]:
  if part.startswith('v33_decode_'):helpers.append(f'FB{fb:02}\nFunction : '+part)
(p/'remat-call-helpers.sass').write_text('\n'.join(helpers))
# Baseline rebuild must be exact; strict candidate HMMA count must not change.
assert candidates['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
for mode,rs in res.items():
 if not mode.startswith('probe_'):assert sum(r['HMMA'] for r in rs.values())==13188
print('source events',probe_counts.keys());print('identity', {m:q['active_text_identical'] for m,q in identity.items()});print('CALLs',sum(r['CALL'] for r in res['remat_call'].values()))

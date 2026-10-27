from pathlib import Path
import json,statistics as st
p=Path(__file__).resolve().parent;rows=json.loads((p/'profile-versions.json').read_text());assert len(rows)==12;out={};lines=['# Fresh NVAPI profiles: V2.2 / V2.4 / V2.6','','Each process 50 warmup / 20 measured frames, order V22→V24→V26 then V26→V24→V22 at each size. Table values average the two per-capture FB means. GPU timestamp intervals include dispatch-local costs and can perturb overlap; whole-frame promotion uses the separate uninstrumented ABBA.','','| Width | FB | Fresh V2.2 ms | Fresh V2.4 ms | Fresh V2.6 ms | V22−V26 ms | V24−V26 ms |','|---:|---:|---:|---:|---:|---:|---:|']
for w in [1280,1920]:
 out[str(w)]={}
 for fb in ['0','1','2','3','4','5','6','13','14']:
  t={v:st.mean(r['by_FB'][fb]['mean_ms'] for r in rows if r['version']==v and r['width']==w) for v in ['v22','v24','v26']};out[str(w)][fb]=t;lines.append(f'| {w} | {fb} | {t["v22"]:.6f} | {t["v24"]:.6f} | {t["v26"]:.6f} | {t["v22"]-t["v26"]:.6f} | {t["v24"]-t["v26"]:.6f} |')
old=json.loads((p.parent/'v23/profile.json').read_text());out['historical_V22_comparison']={w:{'historical_sum_ms':old[w]['sum_kernel_mean_ms'],'fresh_v22_sum_ms':sum(x['v22'] for x in out[w].values()),'fresh_v26_sum_ms':sum(x['v26'] for x in out[w].values())} for w in ['1280','1920']}
lines+=['','Historical V2.2 6.127/11.861ms is shown only as provenance, not mixed into fresh paired deltas. V22→V26 is cumulative progress through multiple versions; it cannot isolate the V2.6 Low/High change. The fresh V24→V26 column addresses that narrower comparison.','',json.dumps(out['historical_V22_comparison'],indent=2)]
(p/'profile-summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'profile-results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:27]))

from pathlib import Path
import json,hashlib,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());base=res['baseline'];out={};chosen=[]
for fb in range(7):
 names=[n for n,r in base.items() if r['FB']==fb];better=any(res['quad_local'][n]['REG']<base[n]['REG'] or res['quad_local'][n]['STACK']<base[n]['STACK'] for n in names);notworse=all(res['quad_local'][n]['REG']<=base[n]['REG'] and res['quad_local'][n]['STACK']<=base[n]['STACK'] for n in names)
 if better and notworse:chosen.append(fb)
 a=json.loads((p/f'quad-audit-quad_local-fb{fb:02}.json').read_text());c=collections.Counter()
 for r in a:c.update(r['rejections'])
 out[fb]={'all_export_fused_pairs':sum(r['fused'] for r in a),'active_fused_pairs':sum(r['fused'] for r in a if r['kernel'] in base),'rejections':dict(c),'active_kernels':{r['kernel']:r for r in a if r['kernel'] in base}}
assert chosen==[1],chosen
# Selected Local Quad module combination is exactly the already requested 0145
# control, because local fusion changes no code in 00/04/05.
for fb in range(15):
 want='quad_local' if fb in chosen else 'baseline';a=p/f'artifacts/{want}/fatbin{fb:02}.cubin';b=p/f'artifacts/quad_fb0145/fatbin{fb:02}.cubin';assert a.read_bytes()==b.read_bytes(),fb
(p/'quad-selection.json').write_text(json.dumps({'chosen_fbs':chosen,'rule':'at least one REG/STACK decrease and no active kernel REG/STACK increase in module; fixed before timing','reused_candidate':'quad_fb0145','reason':'other selected 0145 modules 00/04/05 have no new pairs and are baseline-identical'},indent=2)+'\n');(p/'local-quad-audit.json').write_text(json.dumps(out,indent=2)+'\n')
assert sum(r['all_export_fused_pairs'] for r in out.values())==1688
identity={}
for mode,c in cs.items():
 eq=[(p/f'artifacts/{mode}/fatbin{fb:02}.cubin').read_bytes()==(p/f'artifacts/baseline/fatbin{fb:02}.cubin').read_bytes() for fb in range(15)];identity[mode]={'cubin_equal_to_baseline':eq}
 if mode=='quad_fb1':assert all(eq[i] for i in range(15) if i!=1)
 assert len(c['manifest'])==15 and all(r[1]=='inline' for r in c['manifest'])
(p/'machine-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
print('selected',chosen,'alias quad_fb0145; local fusion totals', {fb:r['all_export_fused_pairs'] for fb,r in out.items()})

#!/usr/bin/env python3
"""Reproduce resource identity and call-weighted static opportunity tables."""
import argparse,collections,csv,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('comparison',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
subprocess.run(['python3',str(repo/'Development/tools/compiler-versions/family-stats.py'),'--comparison','P='+str(a.comparison),'--out',str(a.out)],check=True)
mods={'c32_wave1':'c32-wave1','c64_wave2':'c64-wave2','c512_m32_deep':'c512-m32-deep','c512_m32_mh':'c512-m32-mh','deep':'deep_reference','deep_fast':'deep_fast-packed','mh_fast':'multihead-fast-padded-wave-packed','vit_stream':'vit-stream','mh':'multihead-reference'}
waves={}
for tier in (900,1080):
    c=collections.Counter()
    for r in csv.reader((repo/f'Development/results/kernel-map-20260929/topology-{tier}.csv').open()):
        c[mods[r[1]]+'.hsaco',r[2]]+=int(r[4])*int(r[5])//32
    waves[tier]=c
rows=[]
for r in csv.DictReader((a.out/'active-kernels.csv').open()):
    if r['arch']!='gfx1201':continue
    key=r['module'],r['kernel'];pairs=int(r['candidate_VOPD'])-int(r['baseline_VOPD'])
    rows.append(dict(family=r['family'],module=key[0],kernel=key[1],waves900=waves[900][key],waves1080=waves[1080][key],extra_pairs=pairs,extra_waits=int(r['candidate_WAIT'])-int(r['baseline_WAIT']),static_instruction_delta=int(r['candidate_instructions'])-int(r['baseline_instructions']),pair_wave_proxy1080=pairs*waves[1080][key],note='static body times launch waves; no loop/path weighting; not dynamic instructions'))
rows.sort(key=lambda r:-r['pair_wave_proxy1080'])
with (a.out/'call-weighted-opportunities.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
d=json.loads((a.comparison/'kernel-details.json').read_text());changes=[];count=0
for module,v in d.items():
    for k,b in v['baseline'].items():
        count+=1;c=v['candidate'][k]
        # Compare ALL metadata, not just register totals.
        if b['metadata']!=c['metadata']:changes.append([module,k])
summary=dict(kernels=count,metadata_changed=changes,active_kernel_module_pairs=len(rows),extra_static_pairs=sum(r['extra_pairs'] for r in rows),extra_static_waits=sum(r['extra_waits'] for r in rows),static_instruction_delta=sum(r['static_instruction_delta'] for r in rows))
(a.out/'isa-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)

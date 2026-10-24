#!/usr/bin/env python3
"""Verify coverage, per-frame goldens, finite checks and all AE CSV fields."""
import argparse
import csv
import json
from pathlib import Path

p=argparse.ArgumentParser(__doc__)
p.add_argument('collected',type=Path);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
gold=list(csv.DictReader((repo/'Development/results/float-fma-20260928/new-baseline-hashes.csv').open()))
expected={(r['mode'],r['case'],r['frame']):r['sha'].upper() for r in gold}
rows=list(csv.DictReader((a.collected/'hashes.csv').open(encoding='utf-8-sig')))
assert len(rows)==336,len(rows)
actual={}
for r in rows:
    # The first collector used integer frame IDs. Normalize that naming-only
    # difference; never alter a hash or infer an uncollected frame.
    if r['frame'].isdigit():r['frame']='rgb-frame-'+r['frame']+'.f16'
    mode='AE' if r['batch'].endswith('-adaptive') else 'EXACT'
    candidate=r['slot'].endswith('-True')
    case=r['slot'].rsplit('-',1)[0]
    key=(mode,case,r['frame'],candidate)
    assert key not in actual,key
    actual[key]=r['sha'].upper()
assert {(m,c,f) for m,c,f,b in actual if b}==set(expected)
assert {(m,c,f) for m,c,f,b in actual if not b}==set(expected)
bad=[(key,b) for key,v in expected.items() for b in [False,True] if actual[(*key,b)]!=v]
invalid=0;checked=0;decisions=[]
for mode,batch in [('EXACT','correct'),('AE','adaptive')]:
    for case in sorted({c for m,c,f in expected if m==mode}):
        base=a.collected/f'runtime-regression-L-{batch}'
        for side in ['False','True']:
            frames=list(csv.DictReader((base/f'{case}-{side}'/'rgb.csv').open()))
            assert len(frames)==12
            assert [int(r['frame']) for r in frames]==list(range(12))
            assert all(r['checked']=='1' for r in frames)
            invalid+=sum(int(r['invalid']) for r in frames);checked+=len(frames)
        if mode=='AE':
            b=list(csv.reader((base/f'{case}-False'/'adaptive.csv').open()))
            c=list(csv.reader((base/f'{case}-True'/'adaptive.csv').open()))
            assert len(b)==len(c)==12
            for i,(br,cr) in enumerate(zip(b,c)):
                decisions.append(dict(case=case,row=i+1,equal=br==cr,baseline=br,candidate=cr))
summary=dict(candidate_frames=168,baseline_frames=168,checked_frames=checked,invalid_values=invalid,
             golden_mismatches=bad,ae_rows=len(decisions),ae_unequal_rows=sum(not d['equal'] for d in decisions),
             ae_reuse=sum(d['candidate'][1]=='1' for d in decisions),ae_refresh=sum(d['candidate'][1]=='0' for d in decisions))
summary['pass']=not bad and invalid==0 and summary['ae_unequal_rows']==0
(a.out/'regression-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(a.out/'adaptive-comparison.json').write_text(json.dumps(decisions,indent=2)+'\n')
with (a.out/'hashes.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n");w.writeheader();w.writerows(rows)
print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['pass'] else 1)

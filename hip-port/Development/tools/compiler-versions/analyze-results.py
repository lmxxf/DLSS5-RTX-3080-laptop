#!/usr/bin/env python3
"""Independently check regression coverage and recompute every ABBA slot."""
import argparse,csv,json,statistics
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('--version',required=True);p.add_argument('--collected',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
expected={(r['mode'],r['case'],r['frame']):r['sha'].upper() for r in csv.DictReader((repo/'Development/results/float-fma-20260928/new-baseline-hashes.csv').open())}
rows=list(csv.DictReader((a.collected/f'hashes-{a.version}.csv').open(encoding='utf-8-sig')))
assert len(rows)==336
actual={}
for r in rows:
    mode='AE' if r['batch'].endswith('-adaptive') else 'EXACT'
    key=mode,r['slot'].rsplit('-',1)[0],r['frame'],r['slot'].endswith('-True')
    assert key not in actual;actual[key]=r['sha'].upper()
assert {(m,c,f) for m,c,f,b in actual if b}==set(expected)
assert {(m,c,f) for m,c,f,b in actual if not b}==set(expected)
badbase=[k for k,v in expected.items() if actual[(*k,False)]!=v]
bad=[k for k,v in expected.items() if actual[(*k,True)]!=v]
assert not badbase,('DRIVER BASELINE CHANGED',badbase)
decisions=[];checked=0;invalid=0
for mode,batch in [('EXACT','correct'),('AE','adaptive')]:
    for case in sorted({k[1] for k in expected if k[0]==mode}):
        root=a.collected/f'runtime-regression-{a.version}-{batch}'
        for side in ['False','True']:
            r=list(csv.DictReader((root/f'{case}-{side}'/'rgb.csv').open()))
            assert len(r)==12 and [int(x['frame']) for x in r]==list(range(12))
            assert all(x['checked']=='1' for x in r)
            invalid+=sum(int(x['invalid']) for x in r);checked+=12
        if mode=='AE':
            b=list(csv.reader((root/f'{case}-False'/'adaptive.csv').open()))
            c=list(csv.reader((root/f'{case}-True'/'adaptive.csv').open()))
            assert len(b)==len(c)==12
            decisions.extend(dict(case=case,row=i+1,same=x==y,base=x,candidate=y) for i,(x,y) in enumerate(zip(b,c)))
validation=dict(version=a.version,candidate_frames=168,checked_frames=checked,invalid_values=invalid,changed_frames=bad,ae_changed=sum(not r['same'] for r in decisions),ae_reuse=sum(r['candidate'][1]=='1' for r in decisions))
validation['pass']=not bad and invalid==0 and validation['ae_changed']==0
slots=[];timings=[]
for batch in ['timing1','timing2']:
    root=a.collected/f'runtime-regression-{a.version}-{batch}'
    if not root.exists():continue
    assert validation['pass'],'Timing exists for a numerically rejected compiler'
    for height in (900,1080):
        means=[]
        for slot in range(4):
            r=list(csv.DictReader((root/f'time-{height}-{slot}'/'rgb.csv').open()))
            assert len(r)==1000 and [int(x['frame']) for x in r]==list(range(1000))
            check=[x for x in r if x['checked']=='1'];assert len(check)==2 and all(int(x['invalid'])==0 for x in check)
            vals=[float(x['wall_ms']) for x in r if int(x['frame'])>=200];assert len(vals)==800
            mean=statistics.mean(vals);means.append(mean)
            slots.append(dict(version=a.version,batch=batch,height=height,slot=slot,kind='candidate' if slot in (1,2) else 'driver',frames=800,mean_ms=mean,min_ms=min(vals),max_ms=max(vals)))
        base=(means[0]+means[3])/2;candidate=(means[1]+means[2])/2
        timings.append(dict(version=a.version,batch=batch,height=height,driver_ms=base,candidate_ms=candidate,delta_ms=candidate-base,delta_percent=(candidate/base-1)*100))
(a.out/f'validation-{a.version}.json').write_text(json.dumps(validation,indent=2)+'\n')
(a.out/f'adaptive-{a.version}.json').write_text(json.dumps(decisions,indent=2)+'\n')
for name,data in [('timing-slots',slots),('timings',timings)]:
    (a.out/f'{name}-{a.version}.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(validation=validation,timings=timings),indent=2))

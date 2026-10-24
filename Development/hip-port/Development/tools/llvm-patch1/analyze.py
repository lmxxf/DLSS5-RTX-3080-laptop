#!/usr/bin/env python3
"""Check the seven-case gate and recompute paired public/driver ABBA timings."""
import argparse,csv,json,statistics,subprocess
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('collected',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
subprocess.run(['python3',str(repo/'Development/tools/compiler-versions/analyze-results.py'),'--version','P','--collected',str(a.collected),'--out',str(a.out)],check=True)
assert json.loads((a.out/'validation-P.json').read_text())['pass']
slots=[];results=[]
for batch in ['public1','public2','driver1','driver2']:
    root=a.collected/f'runtime-regression-P-{batch}'
    for height in (900,1080):
        means=[]
        for slot in range(4):
            rows=list(csv.DictReader((root/f'time-{height}-{slot}'/'rgb.csv').open()))
            assert len(rows)==1000 and [int(r['frame']) for r in rows]==list(range(1000))
            checked=[r for r in rows if r['checked']=='1'];assert len(checked)==2 and all(int(r['invalid'])==0 for r in checked)
            values=[float(r['wall_ms']) for r in rows if int(r['frame'])>=200];assert len(values)==800
            mean=statistics.mean(values);means.append(mean)
            slots.append(dict(batch=batch,height=height,slot=slot,kind='patch' if slot in (1,2) else 'baseline',mean_ms=mean,min_ms=min(values),max_ms=max(values),frames=800))
        base=(means[0]+means[3])/2;patch=(means[1]+means[2])/2
        results.append(dict(baseline='public LLVM21' if batch.startswith('public') else 'driver LLVM21',batch=batch,height=height,baseline_ms=base,patch_ms=patch,delta_ms=patch-base,delta_percent=(patch/base-1)*100))
for name,rows in [('timing-slots',slots),('timing-summary',results)]:
    (a.out/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
    with (a.out/(name+'.csv')).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps(results,indent=2))

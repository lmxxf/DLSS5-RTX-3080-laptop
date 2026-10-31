from pathlib import Path
import json,re,statistics as st
p=Path(__file__).resolve().parent;out={};eligible=[];lines=['# V3.6 serial paired results','','Means of process GPU medians, forward ABBA / reverse BAAB; positive = lower latency.','','|Round/candidate|Width|Base ms|Candidate ms|Gain %|Forward %|Reverse %|Quality pass|','|---|---:|---:|---:|---:|---:|---:|---|']
def direction(r):
 m=re.match(r'^(forward|reverse)-',r['name']);assert m;return m[1]
for file in ['timed','repeat']:
 f=p/(('bench' if file=='timed' else file)+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());out[file]={}
 for v in sorted({r['variant'] for r in rows}-{'baseline'}):
  out[file][v]={}
  for w in [1280,1600,1920]:
   rs=[r for r in rows if r['width']==w and re.match(r'^(?:forward|reverse)-'+re.escape(v)+r'-\d+$',r['name'])];assert len(rs)==8
   av=lambda rr:st.mean(r['metrics']['gpu_median_ms'] for r in rr);aa=[r for r in rs if r['variant']=='baseline'];bb=[r for r in rs if r['variant']==v];a,b=av(aa),av(bb);ds={}
   for d in ['forward','reverse']:
    x=[r for r in aa if direction(r)==d];y=[r for r in bb if direction(r)==d];assert len(x)==len(y)==2;ds[d]={'base_ms':av(x),'candidate_ms':av(y),'gain_percent':100*(1-av(y)/av(x))}
   q=all(r['quality']['quality_pass'] for r in bb);rec={'base_ms':a,'candidate_ms':b,'gain_percent':100*(1-b/a),'directions':ds,'quality_pass':q,'PSNR_min_db':min((r['quality']['PSNR_db'] for r in bb if r['quality']['PSNR_db'] is not None),default=None),'maxabs':max(r['quality']['maxabs'] for r in bb)};out[file][v][str(w)]=rec;lines.append(f'|{file}/{v}|{w}|{a:.5f}|{b:.5f}|{rec["gain_percent"]:.3f}|{ds["forward"]["gain_percent"]:.3f}|{ds["reverse"]["gain_percent"]:.3f}|{q}|')
  if file=='timed' and all(r['directions'][d]['gain_percent']>0 for r in out[file][v].values() for d in ['forward','reverse']):eligible.append(v)
(p/'timing-summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'timing-summary.md').write_text('\n'.join(lines)+'\n');(p/'repeat-eligible.json').write_text(json.dumps(eligible,indent=2)+'\n');print('repeat eligible',eligible)

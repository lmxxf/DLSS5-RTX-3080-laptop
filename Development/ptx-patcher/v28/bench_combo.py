from pathlib import Path
import json,sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import bench
bench.variants|=json.loads((p/'combos.json').read_text());bench.rows=[]
# run() writes bench.json, so redirect only that output while preserving initial controls.
original_write=Path.write_text
def write(self,data,*args,**kwargs):
 if self==p/'bench.json':self=p/'combo-bench.json'
 return original_write(self,data,*args,**kwargs)
Path.write_text=write
sys.argv=['bench_combo.py','timed']
for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
 for w in widths:
  order=['baseline','combo','combo','baseline'] if direction=='forward' else ['combo','baseline','baseline','combo']
  for j,v in enumerate(order):bench.run(f'{direction}-combo-{j}',v,w)

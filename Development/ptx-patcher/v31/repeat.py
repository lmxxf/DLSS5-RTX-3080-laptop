from pathlib import Path
import sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import bench
original=Path.write_text
def write(self,data,*args,**kw):
 if self==p/'bench.json':self=p/'repeat.json'
 return original(self,data,*args,**kw)
Path.write_text=write;sys.argv=['repeat.py','timed']
for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
 for w in widths:
  for v in ['pack5','pack5_quad']:
   order=['baseline',v,v,'baseline'] if direction=='forward' else [v,'baseline','baseline',v]
   for j,z in enumerate(order):bench.run(f'repeat-{direction}-{v}-{j}',z,w)

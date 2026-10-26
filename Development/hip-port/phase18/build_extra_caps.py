from pathlib import Path
import sys,json
from concurrent.futures import ProcessPoolExecutor,as_completed
sys.path.insert(0,str(Path(__file__).resolve().parent));from build_controls import job,p
items={
 'all-cap168':{'sites':['contract','result','v','av','byteout'],'cap':168,'qkv':None},
 'all-cap128':{'sites':['contract','result','v','av','byteout'],'cap':128,'qkv':None},
 'fuse7-cap128':{'sites':['byteout'],'cap':128,'qkv':7},
 'pair15-cap128':{'sites':['byteout'],'cap':128,'qkv':15}}
if __name__=='__main__':
 rows=json.loads((p/'control-builds.json').read_text())
 with ProcessPoolExecutor(max_workers=3) as ex:
  for f in as_completed([ex.submit(job,x) for x in items.items()]):n,row=f.result();rows[n]=row
 (p/'control-builds.json').write_text(json.dumps(rows,indent=2)+'\n')

from pathlib import Path
import sys,json,copy,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
base=r/'phase17/artifacts/selected/modules';c32=p/'artifacts/c32-v/modules';w2=p/'artifacts/byteout/modules'
CONFIGS={
 'pack2':{'sites':['byteout'],'cap':None,'qkv':None,'reuse':True},
 'pack-all':{'sites':['contract','result','v','av','byteout'],'cap':None,'qkv':None},
 'cap168':{'sites':['byteout'],'cap':168,'qkv':None},
 'cap128':{'sites':['byteout'],'cap':128,'qkv':None},
 'fuse7':{'sites':['byteout'],'cap':None,'qkv':7},
 'pair15':{'sites':['byteout'],'cap':None,'qkv':15},
 'fuse7-cap168':{'sites':['byteout'],'cap':168,'qkv':7},
 'pair15-cap168':{'sites':['byteout'],'cap':168,'qkv':15}}
def job(item):
 name,cfg=item;out=p/'artifacts'/name/'modules';out.mkdir(parents=True,exist_ok=True)
 for f in base.iterdir():
  if f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_'):continue
  if f.stem=='c64-wave2-fast':
   if not cfg.get('reuse'):continue
   src=w2/f.name
  elif f.stem=='c32-wave1-fast':src=c32/f.name
  else:src=f
  dst=out/f.name
  if not dst.exists():dst.symlink_to(src.resolve())
 if cfg.get('reuse'):return name,{**cfg,'modules':str(out),'result':'reuse independently proven byteout+C32V'}
 b.PHASE18_SITES={'c64-wave2-fast':cfg['sites']};b.PHASE18_C256_CAP=cfg['cap'];b.PHASE18_QKV_MASK=cfg['qkv']
 mod=copy.deepcopy(next(m for m in b.parse_ps1_modules(str(r/'hip/build-modules.ps1')) if m['name']=='c64-wave2-fast'));res=b.compile_one_module(mod,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));print(name,res[:3],flush=True);assert res[1],res
 return name,{**cfg,'modules':str(out),'result':res}
if __name__=='__main__':
 rows={}
 with ProcessPoolExecutor(max_workers=3) as ex:
  for f in as_completed([ex.submit(job,x) for x in CONFIGS.items()]):
   n,row=f.result();rows[n]=row
 (p/'control-builds.json').write_text(json.dumps(rows,indent=2)+'\n')

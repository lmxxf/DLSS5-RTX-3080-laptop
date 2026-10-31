from pathlib import Path
import sys,os,re,json,hashlib,datetime
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b,transform
import v31.codegen as pack
import v26.codegen as v26
from ptx_mapped import Sources
from pe_fatbins import assemble
STOCK_TRANSFORM=b.dp.transform_ptx;LEGACY=v26.render;STOCK_CAP=b.override_maxnreg;MODE='baseline';plans=json.loads((p/'plans.json').read_text());sel=json.loads((p.parent/'v27/selected.json').read_text())
MODES={'baseline':set(range(15)),'fb1_exact_shadow':{1},'fb2_exact_shadow':{2},'fb3_exact_shadow':{3},'fb123_exact_shadow':{1,2,3},'fb1_exact_inplace':{1},'fb1_fast_shadow':{1},'fb1_fast_inplace':{1}}
def worker(task):
 import v22.codegen as v22
 pack.MODE='pack5';v22.pack=pack.pack;v22.declarations=pack.declarations;fb=task[0];target=MODE!='baseline';audit=[];cache={}
 def rewrite(text,*a,**kw):
  if target:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in plans:parts[i]=transform.apply_entry(part,plans[m[1]],MODE)
   text=''.join(parts)
  return STOCK_TRANSFORM(text,*a,**kw)
 b.dp.transform_ptx=rewrite
 def render(ms,sources,*,builder):
  name=re.findall(r'\.visible \.entry (\w+)',ms[0].string[:ms[0].start()])[-1];synthetic=0
  if target and name in plans:
   k=plans[name];key=(name,id(ms[0].string))
   if key not in cache:
    allms=list(builder.dp.FP8_MMA_PATTERN.finditer(ms[0].string));groups=[]
    for m in allms:
     if not groups or ms[0].string[groups[-1][-1].end():m.start()].strip():groups.append([m])
     else:groups[-1].append(m)
    cache[key]={g[0].start():j for j,g in enumerate(groups)}
   run=cache[key][ms[0].start()];byload={l['index']:l for l in k['all_loads']};fake=Sources(sources);fake.until=getattr(sources,'until',{}).copy()
   for event in k['shared_MMA_events']:
    if event['run']!=run:continue
    lo,hi=byload[event['load_index']]['native'][event['component']];fake[event['register']]=(lo,hi,-1);fake.until[event['register']]=float('inf');synthetic+=1
   sources=fake
  rows=[];text=LEGACY(ms,sources,builder=builder,audit=rows);rows[0].update(kernel=name,shared_native_events=synthetic);audit.extend(rows);return text
 v26.render=render
 def cap(text,limit):
  text,n=STOCK_CAP(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in sel['kernel_caps']:parts[i],_=STOCK_CAP(part,sel['kernel_caps'][m[1]])
   text=''.join(parts)
  return text,n
 b.override_maxnreg=cap;start=datetime.datetime.now().isoformat();r=b.worker_compile_fatbin(task);return r,{'FB':fb,'begin':start,'end':datetime.datetime.now().isoformat(),'message':r[2],'runs':audit}
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));cs=json.loads((p/'candidates.json').read_text()) if (p/'candidates.json').exists() else {};records=json.loads((p/'build-records.json').read_text()) if (p/'build-records.json').exists() else {}
 for MODE in sys.argv[1:] or MODES:
  target=MODES[MODE];folder=p/'artifacts'/MODE;folder.mkdir(parents=True,exist_ok=True);os.environ['DLSSNR_BUILD_CACHE']=str(folder);blobs={};rr=[]
  for i in set(range(15))-target:
   for suffix in ['ptx','cubin','bin']:
    dst=folder/f'fatbin{i:02}.{suffix}';src=p/f'artifacts/baseline/fatbin{i:02}.{suffix}'
    if not dst.exists():os.link(src,dst)
   blobs[i]=(folder/f'fatbin{i:02}.bin').read_bytes()
  tasks=[(i,bytes(raw[locs[i].offset:locs[i].offset+locs[i].size]),True,True,'multidef',False,'lowhigh',sel['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',8) for i in sorted(target)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for future in as_completed([pool.submit(worker,t) for t in tasks]):
    r,record=future.result();i,blob,msg=r;assert 'ELF O4' in msg;blobs[i]=blob;rr.append(record);print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(r[1]=='inline' for r in manifest);out=root/f'nvngx_dlssnr_sm86_v35_{MODE}.dll';out.write_bytes(data);cs[MODE]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest,'target_fbs':sorted(target),'approximate':'fast' in MODE};records[MODE]=rr;(p/'candidates.json').write_text(json.dumps(cs,indent=2)+'\n');(p/'build-records.json').write_text(json.dumps(records,indent=2)+'\n')
  if MODE=='baseline':assert cs[MODE]['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'

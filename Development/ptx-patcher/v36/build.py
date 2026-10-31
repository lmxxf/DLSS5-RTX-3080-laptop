from pathlib import Path
import sys,os,re,json,hashlib,datetime
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b,coupled,pack_range,async_shared
import v31.codegen as pack
import v26.codegen as old
from ptx_mapped import Sources
from pe_fatbins import assemble
TRANS=b.dp.transform_ptx;RENDER=old.render;CAP=b.override_maxnreg;LOWER=b.stock_lower_conversions;MODE='baseline';plans=json.loads((p.parent/'v35/plans.json').read_text());sel=json.loads((p.parent/'v27/selected.json').read_text())
MODES={'baseline':set(range(15)),'pack_proven':set(range(7)),'pack4_all':set(range(7)),'fb2_inplace':{2},'fb3_inplace':{3},'fb23_inplace':{2,3},'fb23_fast_inplace':{2,3},'async_fb4':{4},'async_fb5':{5},'async_fb45':{4,5},'fb3_selective_fast_inplace':{3},'fb2_epoch_shadow':{2},'fb2_epoch_fast_shadow':{2}}
def worker(task):
 import v22.codegen as v22
 pack.MODE='pack5';v22.pack=pack.pack;v22.declarations=pack.declarations;fb=task[0];pack_range.AUDIT=[];audits=[];cache={}
 active=MODE.startswith(('fb','async'));useplans=json.loads((p/'async-plans.json').read_text()) if MODE.startswith('async') else plans
 if 'selective' in MODE:useplans={n:k for n,k in plans.items() if n in json.loads((p/'selected-entries.json').read_text())['kernels']}
 if 'epoch' in MODE:useplans=json.loads((p/'epoch-plans.json').read_text())
 def rewrite(text,*a,**kw):
  if active:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in useplans:parts[i]=(async_shared.apply_entry(part,useplans[m[1]],MODE) if MODE.startswith('async') else coupled.apply_entry(part,useplans[m[1]],MODE))
   text=''.join(parts)
  return TRANS(text,*a,**kw)
 b.dp.transform_ptx=rewrite
 def lower(text,stats):return pack_range.lower(text,stats,LOWER,MODE,fb) if MODE.startswith('pack') else LOWER(text,stats)
 # Worker resets lower before this hook is used; install via cap-independent stock binding.
 if MODE.startswith('pack'):b.stock_lower_conversions=lower
 def render(ms,sources,*,builder):
  n=re.findall(r'\.visible \.entry (\w+)',ms[0].string[:ms[0].start()])[-1];count=0
  if active and n in useplans:
   k=useplans[n];key=(n,id(ms[0].string))
   if key not in cache:
    groups=[]
    for m in builder.dp.FP8_MMA_PATTERN.finditer(ms[0].string):
     if not groups or ms[0].string[groups[-1][-1].end():m.start()].strip():groups.append([m])
     else:groups[-1].append(m)
    cache[key]={g[0].start():i for i,g in enumerate(groups)}
   run=cache[key][ms[0].start()];loads={x['index']:x for x in k['all_loads']};fake=Sources(sources);fake.until=getattr(sources,'until',{}).copy()
   for e in k['shared_MMA_events']:
    if e['run']==run:
     lo,hi=loads[e['load_index']]['native'][e['component']];fake[e['register']]=(lo,hi,-1);fake.until[e['register']]=float('inf');count+=1
   sources=fake
  data=[];text=RENDER(ms,sources,builder=builder,audit=data);data[0].update(kernel=n,shared_native_events=count);audits.extend(data);return text
 old.render=render
 def cap(text,limit):
  text,n=CAP(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in sel['kernel_caps']:parts[i],_=CAP(part,sel['kernel_caps'][m[1]])
   text=''.join(parts)
  return text,n
 b.override_maxnreg=cap;start=datetime.datetime.now().isoformat();r=b.worker_compile_fatbin(task);return r,{'FB':fb,'begin':start,'end':datetime.datetime.now().isoformat(),'message':r[2],'runs':audits,'ranges':pack_range.AUDIT}
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));cs=json.loads((p/'candidates.json').read_text()) if (p/'candidates.json').exists() else {};records=json.loads((p/'artifacts/build-records-full.json').read_text()) if (p/'artifacts/build-records-full.json').exists() else {}
 for MODE in sys.argv[1:] or MODES:
  target=MODES[MODE];cache=p/'artifacts'/MODE;cache.mkdir(parents=True,exist_ok=True);os.environ['DLSSNR_BUILD_CACHE']=str(cache);blobs={};rr=[]
  for fb in set(range(15))-target:
   for suffix in ['ptx','cubin','bin']:
    src=p/f'artifacts/baseline/fatbin{fb:02}.{suffix}';dst=cache/f'fatbin{fb:02}.{suffix}'
    if not dst.exists():os.link(src,dst)
   blobs[fb]=(cache/f'fatbin{fb:02}.bin').read_bytes()
  tasks=[(i,bytes(raw[locs[i].offset:locs[i].offset+locs[i].size]),True,True,'multidef',False,'lowhigh',sel['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',8) for i in sorted(target)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(worker,t) for t in tasks]):
    r,d=f.result();i,blob,msg=r;assert 'ELF O4' in msg;blobs[i]=blob;rr.append(d);print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);path=root/f'nvngx_dlssnr_sm86_v36_{MODE}.dll';path.write_bytes(data);cs[MODE]={'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest,'target_fbs':sorted(target),'approximate':('fast' in MODE or MODE.startswith('pack4')),'branch':5 if MODE.startswith('pack') else (6 if MODE.startswith('fb') else 7 if MODE.startswith('async') else 0)};records[MODE]=rr;(p/'candidates.json').write_text(json.dumps(cs,indent=2)+'\n');(p/'artifacts/build-records-full.json').write_text(json.dumps(records));__import__('storage').save_build_summary(records)

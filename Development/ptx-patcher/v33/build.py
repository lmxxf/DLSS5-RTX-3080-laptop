from pathlib import Path
import sys,os,json,re,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b
import v33.codegen as gen
import v31.codegen as pack
import v26.codegen as v26
from pe_fatbins import assemble
LEGACY=v26.render;MODE='baseline';selected=json.loads((p.parent/'v27/selected.json').read_text());stock=b.override_maxnreg
origins=json.loads((p.parent/'v27/source-audit.json').read_text());active={n for ks in origins['fatbins'].values() for n in ks}

def worker(task):
 import v22.codegen as v22
 import v24.codegen as v24
 pack.MODE='pack5';v22.pack=pack.pack;v22.declarations=pack.declarations;v24.quad=pack.quad
 fb=task[0];gen.MODE=MODE;gen.COUNTS={};gen.ORIGINS={n:{(r['run'],r['register']):r for r in d['records']} for ks in origins['fatbins'].values() for n,d in ks.items()}
 runs=[]
 def render(matches,sources,*,builder):
  n=re.findall(r'\.visible \.entry (\w+)',matches[0].string[:matches[0].start()])[-1];a=[]
  target=LEGACY
  if MODE.startswith('phase') and ('guarded' not in MODE or n in json.loads((p/'phase-guarded-targets.json').read_text())['kernels']):target=gen.render;gen.MODE='phase_pass'
  elif MODE.startswith('remat') and ((fb==1 and MODE!='remat_qkv') or (fb==4 and 'qkv_512' in n and MODE!='remat_fb1')):target=gen.render;gen.MODE='remat_call' if MODE=='remat_call' else 'remat'
  elif MODE.startswith('probe_') and n in active:target=gen.render_probe;gen.MODE=MODE
  text=target(matches,sources,builder=builder,audit=a);a[0].update(kernel=n,FB=fb)
  if 'schedule' in a[0]:a[0]['schedule_sha256']=hashlib.sha256(json.dumps(a[0].pop('schedule')).encode()).hexdigest()
  runs.extend(a);return text
 v26.render=render
 def override(text,limit):
  if MODE=='remat_call' and (fb==1 or fb==4):text=text.replace('.address_size 64', '.address_size 64\n'+gen.helper_functions(),1)
  text,n=stock(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in selected['kernel_caps']:parts[i],_=stock(part,selected['kernel_caps'][m[1]])
   text=''.join(parts)
  return text,n
 b.override_maxnreg=override;r=b.worker_compile_fatbin(task)
 (p/f'pool-{MODE}-fb{fb:02}.json').write_text(json.dumps({'runs':runs,'probe_events':gen.COUNTS},indent=2)+'\n');return r
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));rows=json.loads((p/'candidates.json').read_text()) if (p/'candidates.json').exists() else {}
 for MODE in sys.argv[1:] or ['baseline','phase_pass','remat_spill','remat_fb1','remat_qkv','quad_all','quad_fb23','probe_shared','probe_global','probe_mixed','probe_both','probe_all','probe_global_family','remat_call','phase_quad_fb23','phase_guarded','phase_guarded_quad_fb23']:
  os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/MODE);blobs={};tasks=[]
  for i,l in enumerate(locs):
   quad=(MODE=='quad_all' and i in (1,2,3)) or (MODE in ('quad_fb23','phase_quad_fb23','phase_guarded_quad_fb23') and i in (2,3))
   tasks.append((i,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',selected['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',12 if quad else 8))
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(worker,t) for t in tasks]):
    i,blob,msg=f.result();assert 'ELF O4' in msg;blobs[i]=blob;print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(r[1]=='inline' for r in manifest)
  f=root/f'nvngx_dlssnr_sm86_v33_{MODE}.dll';f.write_bytes(data);rows[MODE]={'path':str(f),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest};(p/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n')

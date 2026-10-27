from pathlib import Path
import sys,json,os,re,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
from build_caps import TARGETS
root=Path('/mnt/c/DLSS5-5090-dll');raw=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(raw);loc=locs[0];stock=b.override_maxnreg;rows={};factors=json.loads((p/'factors.json').read_text())
for name,mask,targets,basepath in [('a_cap0',9,TARGETS,Path(factors['a']['path'])),('prefix168',8,{'cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8'},root/'nvngx_dlssnr_sm86_v26.dll')]:
 def override(text,limit):
  text,count=stock(text,limit);parts=re.split(r'(?=\.visible \.entry )',text);changed=0
  for i,part in enumerate(parts):
   m=re.match(r'\.visible \.entry (\w+)',part)
   if m and m[1] in targets:parts[i],n=stock(part,168);assert n==1;changed+=1
  assert changed==len(targets);return ''.join(parts),count
 b.override_maxnreg=override;os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name);_,blob,msg=b.worker_compile_fatbin((0,raw[loc.offset:loc.offset+loc.size],True,True,'multidef',False,'lowhigh',255,'swar','mbarrier','lowhigh8',mask));data,manifest=assemble(basepath.read_bytes(),locs,{0:blob},b.dp);b.fast_update_pe_checksum(data);out=root/f'nvngx_dlssnr_sm86_v27_{name}.dll';out.write_bytes(data);rows[name]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'mask':mask,'kernel_caps':{n:168 for n in sorted(targets)},'base_DLL':str(basepath),'manifest':manifest,'compile':msg};(p/'extra.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,msg,flush=True)

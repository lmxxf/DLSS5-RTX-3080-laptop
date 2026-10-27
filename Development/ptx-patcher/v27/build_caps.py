from pathlib import Path
import sys,os,json,hashlib,re
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
stock_cap=b.override_maxnreg
TARGETS={'cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8','cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8','cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8','cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8'}
def compile_one(task):
 name,fb,cap,blob=task;os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 def override(text,limit):
  text,count=stock_cap(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text);changed=0
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in TARGETS:parts[i],n=stock_cap(part,cap);assert n==1;changed+=1
   assert changed==4;text=''.join(parts)
  return text,count
 b.override_maxnreg=override
 _,out,msg=b.worker_compile_fatbin((fb,blob,True,True,'multidef',False,'lowhigh',255 if fb==0 else cap,'swar','mbarrier','lowhigh8',8));return name,fb,cap,out,msg
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');src=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(src);base=(root/'nvngx_dlssnr_sm86_v26.dll').read_bytes();tasks=[];rows={}
 for fb,caps in [(0,[192,184,168]),(1,[176,184,192])]:
  for cap in caps:
   loc=locs[fb];tasks.append((f'cap{fb}-{cap}',fb,cap,src[loc.offset:loc.offset+loc.size]))
 with ProcessPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(compile_one,t) for t in tasks]):
   name,fb,cap,blob,msg=future.result();assert 'ELF O4' in msg;data,manifest=assemble(base,locs,{fb:blob},b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);out=root/f'nvngx_dlssnr_sm86_v27_{name}.dll';out.write_bytes(data);rows[name]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'FB':fb,'cap':cap,'target_kernels':sorted(TARGETS) if fb==0 else 'all FB01 entries','mask':8,'manifest':manifest,'compile':msg};(p/'caps.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,msg,flush=True)

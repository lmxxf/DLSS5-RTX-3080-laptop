from pathlib import Path
import sys,os,json,hashlib,re
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
stock=b.override_maxnreg
old=json.loads((p.parent/'v27/selected.json').read_text())['kernel_caps']
V='cc_vit_1d_';C='cc_split_swin_16h_'
c=V+'ffn_contract_chained_fp8';q=V+'qkv_chained_fp8';e=[V+'ffn_expand_publish_fp8',V+'ffn_expand_chained_fp8']
CASES={'vit_contract':(5,{c:168}),'vit_cq':(5,{c:168,q:168}),'vit_cqe':(5,{c:168,q:168,**dict.fromkeys(e,168)}),'head':(4,{C+'final_head_512_wait_fp8':128}),'proj':(4,{C+'proj_512_chained_fp8':128}),'pool':(4,{C+'proj_pool_512_chained_fp8':168}),'ffwd_proj':(4,{C+'ffwd_proj_512_chained_fp8':168}),'ffwd_proj_inp':(4,{C+'ffwd_proj_inpview_512_chained_fp8':168}),'ffwd_inp':(4,{C+'ffwd_inpview_512_tilesync_fp8':168}),'up':(0,{'cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8':168})}
def worker(task):
 name,fb,caps,blob=task;os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 targets=(old if fb==0 else {})|caps
 def override(text,limit):
  text,count=stock(text,limit);parts=re.split(r'(?=\.visible \.entry )',text);matched=set()
  for i,part in enumerate(parts):
   m=re.match(r'\.visible \.entry (\w+)',part)
   if m and m[1] in targets:parts[i],n=stock(part,targets[m[1]]);assert n==1;matched.add(m[1])
  assert matched==set(targets);return ''.join(parts),count
 b.override_maxnreg=override
 _,blob,msg=b.worker_compile_fatbin((fb,blob,True,True,'multidef',False,'lowhigh',255,'swar','mbarrier','lowhigh8',8));return name,fb,caps,blob,msg
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');src=(root/'nvngx_dlssnr.dll').read_bytes();base=(root/'nvngx_dlssnr_sm86_v27.dll').read_bytes();assert hashlib.sha256(base).hexdigest()=='28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969';locs=b.dp.find_fatbins(src);tasks=[];rows={}
 for name,(fb,caps) in CASES.items():
  l=locs[fb];tasks.append((name,fb,caps,src[l.offset:l.offset+l.size]))
 with ProcessPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(worker,t) for t in tasks]):
   name,fb,caps,blob,msg=future.result();assert 'ELF O4' in msg;data,manifest=assemble(base,locs,{fb:blob},b.dp);b.fast_update_pe_checksum(data);assert len(data)==len(base) and all(x[1]=='inline' for x in manifest);out=root/f'nvngx_dlssnr_sm86_v28_{name}.dll';out.write_bytes(data);rows[name]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'FB':fb,'caps':caps,'manifest':manifest,'compile':msg};(p/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,msg,flush=True)

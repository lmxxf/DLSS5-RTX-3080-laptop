from pathlib import Path
import sys,os,re,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import v31.codegen as gen
import v32.codegen as split
import v26.codegen as original
MODE="baseline"
RENDER=original.render
DECODE=original.decode
from pe_fatbins import assemble
selected=json.loads((p.parent/'v27/selected.json').read_text());stock=b.override_maxnreg
MODE='baseline'
def worker(task):
 import v22.codegen as v22
 gen.MODE='pack5'
 import v26.codegen as v26
 split.IMMEDIATE='imm' in MODE
 split.SHIFT_MASK='shift' in MODE
 renderer=split.render if 'split' in MODE else RENDER
 runs=[]
 def audited(matches,packed_sources,*,builder):
  audit=[];result=renderer(matches,packed_sources,builder=builder,audit=audit)
  names=re.findall(r'\.visible \.entry (\w+)',matches[0].string[:matches[0].start()])
  audit[0]['kernel']=names[-1] if names else 'unknown';runs.extend(audit);return result
 v26.render=audited
 v26.decode=split.decode if ('imm' in MODE or 'shift' in MODE) else DECODE
 import v24.codegen as v24
 if MODE=='pack5_quad':v24.quad=gen.quad
 v22.declarations=gen.declarations;v22.pack=gen.pack
 fb=task[0]
 def override(text,limit):
  text,n=stock(text,limit)
  if fb in (0,4,5):
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    caps=selected['kernel_caps'] if fb==0 else {}
    targets={'publish':('cc_vit_1d_ffn_expand_publish_fp8',168),'contract':('cc_vit_1d_ffn_contract_chained_fp8',168),'expand':('cc_vit_1d_ffn_expand_chained_fp8',168),'head':('cc_split_swin_16h_final_head_512_wait_fp8',128),'proj':('cc_split_swin_16h_proj_512_chained_fp8',128),'pool':('cc_split_swin_16h_proj_pool_512_chained_fp8',168)}
    suffix=MODE.removeprefix('split_up_')
    if suffix in targets:
     name,cap=targets[suffix];caps={**caps,name:cap}
    if m and m[1] in caps:parts[i],_=stock(part,caps[m[1]])
   text=''.join(parts)
  return text,n
 b.override_maxnreg=override
 result=b.worker_compile_fatbin(task)
 (p/f'pool-{MODE}-fb{fb:02}.json').write_text(json.dumps(runs,indent=2)+'\n')
 return result
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));rows=json.loads((p/'candidates.json').read_text()) if (p/'candidates.json').exists() else {}
 for MODE in sys.argv[1:] or ['baseline','split','up','split_up']:
  os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/MODE);blobs={};tasks=[(i,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',selected['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',9 if 'up' in MODE else 8) for i,l in enumerate(locs)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(worker,t) for t in tasks]):
    i,blob,msg=f.result();assert 'ELF O4' in msg;blobs[i]=blob;print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);out=root/f'nvngx_dlssnr_sm86_v32_{MODE}.dll';out.write_bytes(data);rows[MODE]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest};(p/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n')

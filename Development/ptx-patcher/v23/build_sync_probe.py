"""Destructive synchronization ablation, DIAGNOSTIC ONLY, never recommended.
Replace only signed ready-flag poll loads (ready iff > -1) by 0 and remove
fences. Publication stores/atomics, mbarrier, bar.sync and math stay intact.
Even output equality would not prove general concurrency correctness.
"""
from pathlib import Path
import sys,re,json,os,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
mode=sys.argv[1] if len(sys.argv)>1 else 'bypass'
assert mode in ['bypass','nosleep']
original=b.dp.transform_ptx;stats={}
def probe(source,target,**kwargs):
 out,st=original(source,target,**kwargs)
 if mode=="nosleep":
  out,n=re.subn(r"nanosleep\.u32\s+%r\d+;", "", out);st.add("diagnostic_nosleep",n);return out,st
 # Match the consumer's exact readiness test; do not replace arbitrary loads.
 pattern=r'ld\.relaxed\.gpu\.global\.L1::no_allocate\.s32\s+(%r\d+),\s*\[%rd\d+\];(?=\s*setp\.gt\.s32\s+%p\d+,\s*\1,\s*-1;)'
 out,n=re.subn(pattern,r'mov.b32 \1, 0;',out);out,nf=re.subn(r'fence\.acq_rel\.gpu;', '',out);st.add('diagnostic_ready_bypass',n);st.add('diagnostic_fence_remove',nf);return out,st
b.dp.transform_ptx=probe
src=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes());locs=b.dp.find_fatbins(src);base=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v22.dll').read_bytes());cache=p/'artifacts'/mode;os.environ['DLSSNR_BUILD_CACHE']=str(cache);blobs={}
for i in range(7):
 loc=locs[i];_,blob,msg=b.worker_compile_fatbin((i,bytes(src[loc.offset:loc.offset+loc.size]),True,True,'multidef',False,'evenodd',255 if i in [0,3,4,5,6] else None,'swar','mbarrier'));blobs[i]=blob;stats[str(i)]=msg;print(i,msg,flush=True)
base,manifest=assemble(base,locs,blobs,b.dp);b.fast_update_pe_checksum(base);out=Path('/mnt/c/DLSS5-5090-dll')/f'nvngx_dlssnr_v23_{mode}_DIAGNOSTIC.dll';out.write_bytes(base);(p/('sync-probe-build.json' if mode=='bypass' else 'nosleep-build.json')).write_text(json.dumps({'path':str(out),'sha256':hashlib.sha256(base).hexdigest(),'stats':stats,'manifest':manifest,'diagnostic_only':True},indent=2)+'\n')

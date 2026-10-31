"""Fresh diagnostic 2x2 on frozen pack5. Never eligible for promotion."""
from pathlib import Path
import sys,importlib.util,hashlib,json
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p.parent.parent/'doc'))
import eval_20261029_2000_probes as e
e.TMP=p/'artifacts/probes';e.TMP.mkdir(parents=True,exist_ok=True)
if __name__=='__main__':
 rows={}
 for short,mode in [('p0','p0_zeropack'),('p1','p1_v31_zerodecode'),('p2','p2_zerodecode_zeropack')]:
  blobs=dict(e.v27_blobs);tasks=[(i,bytes(e.raw_orig[l.offset:l.offset+l.size]),mode) for i,l in enumerate(e.orig_locs) if i<7]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(e.worker_probe,t) for t in tasks]):
    i,blob,msg=f.result();assert 'ELF O4' in msg;blobs[i]=blob;print(short,i,msg,flush=True)
  data,manifest=e.assemble(bytearray(e.raw_orig),e.orig_locs,blobs,e.b.dp);e.b.fast_update_pe_checksum(data);out=e.ROOT/f'nvngx_dlssnr_sm86_v32_probe_{short}.dll';out.write_bytes(data);rows['probe_'+short]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest}
  (p/'probes.json').write_text(json.dumps(rows,indent=2)+'\n')

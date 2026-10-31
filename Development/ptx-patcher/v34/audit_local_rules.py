"""Source-only lowering stops before any CUDA context or compilation."""
from pathlib import Path
import json,sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import build
class Stop(Exception):pass
def stop(*args):raise Stop()
build.stock=stop;build.MODE='quad_local';root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());build.b.dp.strip_authenticode(raw);ls=build.b.dp.find_fatbins(raw);build.b.dp.apply_host_patches(raw,(build.b.dp.AMPERE,))
for fb in range(7):
 old=json.loads((p/f'quad-audit-quad_local-fb{fb:02}.json').read_text());l=ls[fb];task=(fb,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',build.selected['base_caps'].get(str(fb)),'swar','mbarrier','lowhigh8',12)
 try:build.worker(task)
 except Stop:pass
 rows=build.local_quad.AUDIT;assert sum(r['fused'] for r in rows)==sum(r['fused'] for r in old);(p/f'quad-audit-quad_local-fb{fb:02}.json').write_text(json.dumps(rows,indent=2)+'\n');print(fb,sum(r['fused'] for r in rows),next((r['rejection_examples'] for r in rows if r['rejection_examples']),[]),flush=True)

from pathlib import Path
import sys,json,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll');source=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(source);base=(root/'nvngx_dlssnr_sm86_v24.dll').read_bytes();blob=(p/'artifacts/decode/fatbin00.bin').read_bytes();out,manifest=assemble(base,locs,{0:blob},b.dp);b.fast_update_pe_checksum(out);path=root/'nvngx_dlssnr_sm86_v25_fb0.dll';path.write_bytes(out);(p/'fb0-build.json').write_text(json.dumps({'path':str(path),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'manifest':manifest},indent=2)+'\n')

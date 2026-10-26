from pathlib import Path
import sys,json,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll');src=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(src);base=(root/'nvngx_dlssnr_sm86_v2.dll').read_bytes();caps={4:255,5:255};blobs={i:(p/f'artifacts/fb{i:02d}-cap255/fatbin{i:02d}.bin').read_bytes() for i in caps};data,manifest=assemble(base,locs,blobs,b.dp);b.fast_update_pe_checksum(data);out=root/'nvngx_dlssnr_sm86_v21_fb45.dll';out.write_bytes(data);d=json.loads((p/'build-results.json').read_text());d['variants']['fb45']={'path':str(out),'caps':caps,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest};(p/'build-results.json').write_text(json.dumps(d,indent=2)+'\n');print(d['variants']['fb45'])

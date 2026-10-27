from pathlib import Path
import sys,json,hashlib,datetime
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import build
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll');raw=(root/'nvngx_dlssnr.dll').read_bytes();base=(root/'nvngx_dlssnr_sm86_v27.dll').read_bytes();locs=build.b.dp.find_fatbins(raw);candidates=json.loads((p/'candidates.json').read_text());caps=candidates['pool']['caps']|candidates['proj']['caps'];fb=4;l=locs[fb];begin=datetime.datetime.now().isoformat();name,fb,caps,blob,msg=build.worker(('combo',fb,caps,raw[l.offset:l.offset+l.size]));assert 'ELF O4' in msg
up=(p/'artifacts/up/fatbin00.bin').read_bytes();assert up[:4]==b'\x50\xed\x55\xba';data,manifest=assemble(base,locs,{0:up,4:blob},build.b.dp);build.b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);out=root/'nvngx_dlssnr_sm86_v28_combo.dll';out.write_bytes(data);row={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'caps':caps|candidates['up']['caps'],'manifest':manifest,'compile':msg,'begin':begin,'end':datetime.datetime.now().isoformat()};(p/'combos.json').write_text(json.dumps({'combo':row},indent=2)+'\n');print(row)

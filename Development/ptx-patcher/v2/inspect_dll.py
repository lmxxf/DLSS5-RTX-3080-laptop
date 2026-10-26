from pathlib import Path
import sys,struct,json,hashlib,ctypes as c,subprocess,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
root=Path('/mnt/c/DLSS5-5090-dll');paths={'old':root/'nvngx_dlssnr_sm86_fast.dll','v7':root/'discord_v7/nvngx_dlssnr_309_v2i8_255_rtx2030_V7.dll','new':root/'nvngx_dlssnr_sm86_v2.dll'}
art=p/'artifacts';tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;rows={}
for tag,path in paths.items():
 if not path.exists():continue
 data=path.read_bytes();locs=d.find_fatbins(data);secs=d.read_pe_sections(data);r={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'sections':[vars(s) for s in secs],'fatbin_count':len(locs),'fatbins':[]};out=art/tag;out.mkdir(parents=True,exist_ok=True)
 for i,loc in enumerate(locs):
  blob=data[loc.offset:loc.offset+loc.size];records=d.parse_fatbin_records(blob);meta={'index':i,'offset':loc.offset,'bytes':loc.size,'records':[]}
  for j,rec in enumerate(records):
   hdr=blob[rec.offset:rec.offset+rec.header_size];arch=struct.unpack_from('<I',hdr,28)[0];a={'kind':rec.kind,'arch':arch,'flags':rec.flags};meta['records'].append(a)
   if rec.kind!=2 or arch not in [75,80,86,89,90,120]:continue
   payload=blob[rec.offset+rec.header_size:rec.offset+rec.header_size+rec.payload_size]
   if rec.flags&0x8000:
    comp=struct.unpack_from('<I',hdr,16)[0];usize=struct.unpack_from('<Q',hdr,56)[0];dst=c.create_string_buffer(usize);ret=z.ZSTD_decompress(dst,c.c_size_t(usize),payload,c.c_size_t(comp));assert ret==usize;(out/f'fb{i:02d}-sm{arch}.cubin').write_bytes(dst.raw)
   else:(out/f'fb{i:02d}-sm{arch}.cubin').write_bytes(payload)
  r['fatbins'].append(meta)
 rows[tag]=r
(p/'dll-layouts.json').write_text(json.dumps(rows,indent=2)+'\n');print({tag:(r['bytes'],r['fatbin_count'],r['sections']) for tag,r in rows.items()})

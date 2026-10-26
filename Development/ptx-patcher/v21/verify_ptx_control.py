from pathlib import Path
import json,sys,ctypes as c,struct,re,hashlib
from functools import partial
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
src=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(src);z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t
b.dp.fp8_conversion_declarations=b.fast_fp8_conversion_declarations;b.dp.fp8_pair_to_half_lines=b.fast_fp8_pair_to_half_lines;b.dp.half_conversion_declarations=b.fast_half_conversion_declarations;b.dp.half_pair_to_fp8_lines=b.fast_half_pair_to_fp8_lines;b.dp.render_fp8_mma_run=b.fast_render_fp8_mma_run;b.dp.fp8_pack_sources=partial(b.stock_pack_sources,local_only=False);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources
rows={}
for f in sorted((p/'artifacts').glob('fb*-cap*/fatbin*.ptx')):
 i=int(re.search(r'fatbin(\d+)',f.name)[1]);loc=locs[i];blob=src[loc.offset:loc.offset+loc.size];rec=next(r for r in b.dp.parse_fatbin_records(blob) if r.kind==1);hdr=blob[rec.offset:rec.offset+rec.header_size];raw=blob[rec.offset+rec.header_size:rec.offset+rec.header_size+rec.payload_size]
 if rec.flags&0x8000:
  comp=struct.unpack_from('<I',hdr,16)[0];usize=struct.unpack_from('<Q',hdr,56)[0];dst=c.create_string_buffer(usize);assert z.ZSTD_decompress(dst,c.c_size_t(usize),raw,c.c_size_t(comp))==usize;raw=dst.raw
 baseline,_=b.dp.transform_ptx(raw.decode().rstrip('\0'),b.dp.AMPERE);candidate=f.read_text();norm=lambda t:re.sub(r'(?m)^(\s*\.maxnreg\s+)\d+',lambda m:m[1]+'CAP',t)
 assert norm(baseline)==norm(candidate),f
 rows[f.parent.name]={'only_existing_maxnreg_changed':True,'old_caps':{n:len(re.findall(r'\.maxnreg\s+'+n+r'\b',baseline)) for n in set(re.findall(r'\.maxnreg\s+(\d+)',baseline))},'new_caps':sorted(set(map(int,re.findall(r'\.maxnreg\s+(\d+)',candidate)))),'normalized_PT X_sha256'.replace(' ',''):hashlib.sha256(norm(candidate).encode()).hexdigest()}
(p/'ptx-controls.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'controls: only .maxnreg literals differ from V2 PTX')

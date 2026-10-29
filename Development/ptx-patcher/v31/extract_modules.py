from pathlib import Path
import sys,ctypes as c,struct,json,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v29_fast.dll').read_bytes();assert hashlib.sha256(raw).hexdigest()=='55b518762bbe4d43fbe71f838352e23584d719736d86dd45437f4f50fc135f5c';z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;dest=p/'artifacts/baseline';dest.mkdir(parents=True,exist_ok=True)
for fb,loc in enumerate(d.find_fatbins(raw)):
 blob=raw[loc.offset:loc.offset+loc.size];r=next(x for x in d.parse_fatbin_records(blob) if x.kind==2);h=blob[r.offset:r.offset+r.header_size];src=blob[r.offset+r.header_size:r.offset+r.header_size+r.payload_size];size=struct.unpack_from('<Q',h,56)[0];n=struct.unpack_from('<I',h,16)[0];out=c.create_string_buffer(size);assert z.ZSTD_decompress(out,c.c_size_t(size),src,c.c_size_t(n))==size;(dest/f'fatbin{fb:02}.cubin').write_bytes(out.raw)

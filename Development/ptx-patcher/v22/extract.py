from pathlib import Path
import sys,ctypes as C,struct,json
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
out=p/'artifacts/raw';out.mkdir(parents=True,exist_ok=True);src=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes();z=C.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=C.c_size_t
for i,loc in enumerate(d.find_fatbins(src)):
 blob=src[loc.offset:loc.offset+loc.size];rec=next(r for r in d.parse_fatbin_records(blob) if r.kind==1);hdr=blob[rec.offset:rec.offset+rec.header_size];raw=blob[rec.offset+rec.header_size:rec.offset+rec.header_size+rec.payload_size]
 if rec.flags&0x8000:
  n=struct.unpack_from('<Q',hdr,56)[0];c=struct.unpack_from('<I',hdr,16)[0];dst=C.create_string_buffer(n);assert z.ZSTD_decompress(dst,C.c_size_t(n),raw,C.c_size_t(c))==n;raw=dst.raw
 (out/f'fb{i:02d}.ptx').write_bytes(raw.rstrip(b'\0'))

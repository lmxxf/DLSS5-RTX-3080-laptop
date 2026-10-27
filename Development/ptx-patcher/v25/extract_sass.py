from pathlib import Path
import sys,ctypes as c,struct,subprocess
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll').read_bytes();z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
for i,loc in enumerate(d.find_fatbins(raw)):
 if i not in [4,5]:continue
 blob=raw[loc.offset:loc.offset+loc.size];r=next(x for x in d.parse_fatbin_records(blob) if x.kind==2);h=blob[r.offset:r.offset+r.header_size];src=blob[r.offset+r.header_size:r.offset+r.header_size+r.payload_size];size=struct.unpack_from('<Q',h,56)[0];n=struct.unpack_from('<I',h,16)[0];out=c.create_string_buffer(size);assert z.ZSTD_decompress(out,c.c_size_t(size),src,c.c_size_t(n))==size;f=p/f'artifacts/base-fb{i:02}.cubin';f.write_bytes(out.raw);s=subprocess.check_output([tool,'-sass',str(f)],text=True,stderr=subprocess.DEVNULL);(p/f'artifacts/base-fb{i:02}.sass').write_text(s)

from pathlib import Path
import sys,re,json,collections,bisect,struct,ctypes as c
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));sys.path.insert(0,str(p.parent/'v25'))
import build_sm86_dlls as b,ptx_mapped,cfg_loops
src=(p.parent/'v27/source_audit.py').read_text();ns=dict(re=re,bisect=bisect,collections=collections,REG=re.compile(r'%[A-Za-z_]+\d+'),parse=cfg_loops.parse);exec(src[src.index('def split_args'):src.index('\nresult={};all_peaks={}')],ns);Origin=ns['Origin'];split_args=ns['split_args'];REG=ns['REG']
def raw_modules():
 raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes();z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t
 for fb,loc in enumerate(b.dp.find_fatbins(raw)[:7]):
  blob=raw[loc.offset:loc.offset+loc.size];r=next(r for r in b.dp.parse_fatbin_records(blob) if r.kind==1);h=blob[r.offset:r.offset+r.header_size];v=struct.unpack_from('<HHIQIIIIIIQQQ',h);payload=blob[r.offset+v[2]:r.offset+v[2]+(v[4] or v[3])]
  if v[10]&0x8000:
   out=c.create_string_buffer(v[12]);assert z.ZSTD_decompress(out,c.c_size_t(v[12]),payload,c.c_size_t(len(payload)))==v[12];payload=out.raw
  yield fb,payload.decode().rstrip('\0')
def entries(text):
 for part in re.split(r'(?=\.visible \.entry )',text)[1:]:yield re.match(r'\.visible \.entry (\w+)',part)[1],part

from pathlib import Path
import sys,ctypes,struct,re,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as dp
z=ctypes.CDLL('libzstd.so.1');z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];z.ZSTD_decompress.restype=ctypes.c_size_t
raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes()
for i,l in enumerate(dp.find_fatbins(raw)):
 blob=raw[l.offset:l.offset+l.size];rec=next(r for r in dp.parse_fatbin_records(blob) if r.kind==1)
 h=struct.unpack_from('<HHIQIIIIIIQQQ',blob,rec.offset);payload=blob[rec.offset+h[2]:rec.offset+h[2]+(h[4] or h[3])]
 if h[10]&0x8000:
  dst=ctypes.create_string_buffer(h[12]);assert z.ZSTD_decompress(dst,h[12],payload,len(payload))==h[12];payload=dst.raw
 txt=payload.decode().rstrip('\0');Path('/tmp/dlss-sky-audit/fatbin%02d.ptx'%i).write_text(txt)
 blocks=[]
 for e in re.finditer(r'elect\.sync\s+_\|([\w%]+),[^;]+;',txt):
  tail=txt[e.end():e.end()+1500]
  sel=re.search(r'selp\.b32\s+(%r\d+),\s*1,\s*0,\s*'+re.escape(e[1])+r'\s*;',tail)
  if not sel: continue
  pred=re.search(r'setp\.eq\.b32\s+(%p\d+),\s*'+re.escape(sel[1])+r',\s*0\s*;',tail)
  if not pred: continue
  branch=re.search(r'@'+re.escape(pred[1])+r'\s+bra\s+([\w$]+)\s*;',tail)
  if branch:
   start=e.end()+branch.end();end=txt.find(branch[1]+':',start);blocks.append(re.split(r'bra\.uni\s+',txt[start:end])[0])
 counts=collections.Counter()
 for b in blocks:
  for line in b.splitlines():
   line=line.strip()
   if line and not line.startswith(('//','{','}')):counts[line.split()[0]]+=1
 print(i,'elect_blocks',len(blocks),'instructions',dict(counts))
 if i<7:Path('/tmp/dlss-sky-audit/elect%02d.txt'%i).write_text('\n\n'.join(blocks))

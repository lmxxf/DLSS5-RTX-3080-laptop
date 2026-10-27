from pathlib import Path
import sys,ctypes as c,struct,subprocess,re,json,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
profile=json.loads((p/'profile.json').read_text());wanted={r['name'] for w in profile.values() for r in w['calls']};z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';result={}
for tag,dll in [('baseline','/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v22.dll'),('decode','/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v23_decode.dll')]:
 data=Path(dll).read_bytes();result[tag]={};dest=p/'artifacts'/tag;dest.mkdir(exist_ok=True)
 for i,loc in enumerate(d.find_fatbins(data)):
  blob=data[loc.offset:loc.offset+loc.size];rec=next(r for r in d.parse_fatbin_records(blob) if r.kind==2);hdr=blob[rec.offset:rec.offset+rec.header_size];payload=blob[rec.offset+rec.header_size:rec.offset+rec.header_size+rec.payload_size]
  if rec.flags&0x8000:
   comp=struct.unpack_from('<I',hdr,16)[0];usize=struct.unpack_from('<Q',hdr,56)[0];dst=c.create_string_buffer(usize);assert z.ZSTD_decompress(dst,c.c_size_t(usize),payload,c.c_size_t(comp))==usize;payload=dst.raw
  path=dest/f'fatbin{i:02d}.cubin';path.write_bytes(payload);sass=subprocess.check_output([tool,'-sass',str(path)],text=True)
  for ch in sass.split('Function : ')[1:]:
   name=ch.splitlines()[0].strip()
   if name not in wanted:continue
   ops=collections.Counter(re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?[UP]+\d+\s+)?([A-Z][A-Z0-9_.]+)',ch));base=collections.Counter()
   for op,n in ops.items():base[op.split('.')[0]]+=n
   result[tag][name]={'FB':i,'static_SASS_instructions':sum(ops.values()),'full_opcodes':dict(ops),'families':dict(base)}
(p/'sass-audit.json').write_text(json.dumps(result,indent=2)+'\n')
for name in sorted(wanted):
 a=result['baseline'][name];b=result['decode'][name]
 if a['FB'] in [0,5]:print(name,a['static_SASS_instructions'],'->',b['static_SASS_instructions'],'PRMT',a['families'].get('PRMT',0),'->',b['families'].get('PRMT',0),'HMMA',a['families'].get('HMMA',0),flush=True)

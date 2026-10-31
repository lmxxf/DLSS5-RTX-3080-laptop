from pathlib import Path
import struct,json,hashlib
p=Path(__file__).resolve().parent;active=json.loads((p/'resources.json').read_text())['baseline']
def sections(path):
 d=path.read_bytes();assert d[:6]==b'\x7fELF\x02\x01';off=struct.unpack_from('<Q',d,40)[0];size,num,strings=struct.unpack_from('<HHH',d,58);heads=[struct.unpack_from('<IIQQQQIIQQ',d,off+i*size) for i in range(num)];sh=heads[strings];names=d[sh[4]:sh[4]+sh[5]];out={}
 for h in heads:
  name=names[h[0]:].split(b'\0')[0].decode()
  if name.startswith('.text.'):out[name[6:]]=d[h[4]:h[4]+h[5]]
 return out
out={}
for mode,reference in [('shift','baseline'),('split_up_shift','split_up')]:
 rows={}
 for fb in range(7):
  a=sections(p/f'artifacts/{mode}/fatbin{fb:02}.cubin');b=sections(p/f'artifacts/{reference}/fatbin{fb:02}.cubin')
  for n,r in active.items():
   if r['FB']==fb:rows[n]={'byte_identical':a[n]==b[n],'candidate_sha256':hashlib.sha256(a[n]).hexdigest(),'reference_sha256':hashlib.sha256(b[n]).hexdigest()}
 out[mode]={'reference':reference,'kernels':rows};print(mode,'changed active .text',sum(not r['byte_identical'] for r in rows.values()))
(p/'shift-text-equivalence.json').write_text(json.dumps(out,indent=2)+'\n')

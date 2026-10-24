from pathlib import Path
import struct,ctypes,ctypes.util,json,collections,re,sys,hashlib
P=Path(sys.argv[1]);b=(P/'gfx1201.hsaco').read_bytes();h=struct.unpack_from('<16sHHIQQQIHHHHHH',b);ss=[struct.unpack_from('<IIQQQQIIQQ',b,h[6]+i*h[11]) for i in range(h[12])];out={}
for s in ss:
 if s[1]==7:
  p=s[4];end=p+s[5]
  while p+12<=end:
   ns,ds,t=struct.unpack_from('<III',b,p);p+=12;name=b[p:p+ns];p+=(ns+3)&~3;desc=b[p:p+ds];p+=(ds+3)&~3
   if name.rstrip(b'\0')==b'AMDGPU':
    import msgpack
    meta=msgpack.unpackb(desc,raw=False);(P/'metadata.json').write_text(json.dumps(meta,indent=2))
 if s[1] not in (2,11):continue
 st=ss[s[6]];strings=b[st[4]:st[4]+st[5]]
 for off in range(s[4],s[4]+s[5],s[9]):
  n,info,other,idx,val,size=struct.unpack_from('<IBBHQQ',b,off)
  if info&15!=2 or not 0<idx<len(ss):continue
  name=strings[n:].split(b'\0')[0].decode();sec=ss[idx];pos=sec[4]+val-sec[3];out[name]=(val,b[pos:pos+size])
l=ctypes.CDLL(sys.argv[2] if len(sys.argv)>2 else ctypes.util.find_library('LLVM-20'))
for n in ('LLVMInitializeAMDGPUTargetInfo','LLVMInitializeAMDGPUTarget','LLVMInitializeAMDGPUTargetMC','LLVMInitializeAMDGPUDisassembler'):getattr(l,n)()
l.LLVMCreateDisasmCPUFeatures.restype=ctypes.c_void_p;l.LLVMCreateDisasmCPUFeatures.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p]
l.LLVMDisasmInstruction.restype=ctypes.c_size_t;l.LLVMDisasmInstruction.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint64,ctypes.c_uint64,ctypes.c_char_p,ctypes.c_size_t]
c=l.LLVMCreateDisasmCPUFeatures(b'amdgcn-amd-amdhsa',b'gfx1201',b'',None,0,None,None)
(P/'isa').mkdir(exist_ok=True);summary=[]
md={k['.name']:k for k in meta['amdhsa.kernels']}
for name,(addr,data) in sorted(out.items()):
 buf=ctypes.create_string_buffer(data);txt=ctypes.create_string_buffer(2048);lines=[];counts=collections.Counter();offset=0;unknown=0
 while offset<len(data):
  n=l.LLVMDisasmInstruction(c,ctypes.byref(buf,offset),len(data)-offset,addr+offset,txt,2048)
  if not n:
   text=f'.long 0x{int.from_bytes(data[offset:offset+4],"little"):08x}';n=4;unknown+=1
  else:text=txt.value.decode().strip()
  lines.append(f'{addr+offset:08x}: {text}');counts[text.split()[0] if text else 'empty']+=1;offset+=n
 (P/'isa'/f'{name}.s').write_text('\n'.join(lines)+'\n')
 m=md.get(name,{})
 summary.append({'name':name,'code_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'unknown':unknown,'instructions':dict(counts),'resources':{k:v for k,v in m.items() if k not in ('.args',)}})
(P/'kernels.json').write_text(json.dumps(summary,indent=2))
print('functions',len(summary),'unknown',sum(x['unknown'] for x in summary))

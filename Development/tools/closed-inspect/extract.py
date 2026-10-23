"""Statically extract embedded PE DLL and clang GPU bundles; never execute setup."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
b=source.read_bytes();magic=b'__CLANG_OFFLOAD_BUNDLE__';base=b.index(magic)
p=base+len(magic);n=struct.unpack_from('<Q',b,p)[0];p+=8
assert 0<n<64
manifest={'input':str(source),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'bundle_offset':base,'entries':[]}
for i in range(n):
    offset,size,length=struct.unpack_from('<QQQ',b,p);p+=24
    assert length<1024 and p+length<=len(b)
    name=b[p:p+length].decode();p+=length
    assert base+offset+size<=len(b)
    blob=b[base+offset:base+offset+size]
    manifest['entries'].append({'name':name,'offset':offset,'size':size,'sha256':hashlib.sha256(blob).hexdigest()})
    if size and name.startswith('hip'):
        arch=name.split('--')[-1]
        assert re.fullmatch(r'[A-Za-z0-9_-]+',arch)
        (out/(arch+'.hsaco')).write_bytes(blob)

for match in re.finditer(b'MZ',b):
    start=match.start()
    if start==0 or start+64>=len(b):continue
    pe=start+struct.unpack_from('<I',b,start+60)[0]
    if pe+24>=len(b) or b[pe:pe+4]!=b'PE\0\0':continue
    count=struct.unpack_from('<H',b,pe+6)[0]
    options,characteristics=struct.unpack_from('<HH',b,pe+20)
    if not characteristics&0x2000 or not 0<count<96:continue
    table=pe+24+options;end=0;sections=[]
    if table+40*count>len(b):continue
    for i in range(count):
        pos=table+40*i
        vsize,rva,size,raw=struct.unpack_from('<IIII',b,pos+8)
        end=max(end,raw+size)
        sections.append({'name':b[pos:pos+8].rstrip(b'\0').decode(),'rva':rva,'raw':raw,'size':size,'vsize':vsize})
    if start<=base<start+end<=len(b):
        dll=b[start:start+end];(out/'mod.dll').write_bytes(dll)
        manifest['dll']={'offset':start,'size':end,'sha256':hashlib.sha256(dll).hexdigest(),'sections':sections}
        break
assert 'dll' in manifest,'embedded DLL not found'
(out/'extraction.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('extracted',manifest['sha256'],len(manifest['entries']),'bundle entries')

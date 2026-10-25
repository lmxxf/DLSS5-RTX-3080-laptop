#!/usr/bin/env python3
"""Compare ELF cubin kernel machine-code sections without disassembler tooling."""
import struct,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def sections(path):
    b=path.read_bytes()
    assert b[:6]==b'\x7fELF\x02\x01'
    off=struct.unpack_from('<Q',b,40)[0];stride,n,idx=struct.unpack_from('<HHH',b,58)
    rows=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*stride) for i in range(n)]
    r=rows[idx];strings=b[r[4]:r[4]+r[5]]
    return {strings[r[0]:strings.index(b'\0',r[0])].decode():b[r[4]:r[4]+r[5]] for r in rows}
records=[]
for module,entry in [('c64-wave2-fast','c128_wave2_bi_bo'),('vit-stream-fast','vit_stream_contract_frag_bstream_bout_compactw_w16'),('vit-stream-fast','vit_stream_qkv_frag_bin_w5f8'),('deep_fast-packed-fast','vit_expand_blocked_fp8_frag_bytein_w16')]:
    a=sections(root/'phase2/artifacts/modules'/f'{module}.hsaco')['.text.'+entry]
    b=sections(root/'phase3/artifacts/modules'/f'{module}.hsaco')['.text.'+entry]
    records.append({'module':module,'kernel':entry,'phase2_bytes':len(a),'phase3_bytes':len(b),'identical':a==b,'phase2_sha256':hashlib.sha256(a).hexdigest(),'phase3_sha256':hashlib.sha256(b).hexdigest()})
print(json.dumps(records,indent=2));(root/'phase3/kernel-text-comparison.json').write_text(json.dumps(records,indent=2)+'\n')

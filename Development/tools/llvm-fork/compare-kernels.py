#!/usr/bin/env python3
"""ELF function bytes, disassembled static instructions and AMDGPU resources.

Counts are static, not executed instruction totals or predictions of frame time.
Requires msgpack (AMDGPU metadata) and the built llvm-objdump.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
import msgpack


def elf(path):
    d = path.read_bytes()
    if d[:6] != b'\x7fELF\x02\x01':
        raise ValueError(f'Not little-endian ELF64: {path}')
    shoff = struct.unpack_from('<Q', d, 40)[0]
    sz, num, names = struct.unpack_from('<HHH', d, 58)
    hdr = [struct.unpack_from('<IIQQQQIIQQ', d, shoff + i*sz) for i in range(num)]
    strings = d[hdr[names][4]:hdr[names][4]+hdr[names][5]]
    def cstr(buf, start):
        return buf[start:buf.index(b'\0', start)].decode()
    sections, kernels, symbols = {}, {}, {}
    for h in hdr:
        name = cstr(strings, h[0])
        buf = d[h[4]:h[4]+h[5]] if h[1] != 8 else b''
        sections[name] = buf
        if h[1] == 7:
            off = 0
            while off + 12 <= len(buf):
                ns, ds, typ = struct.unpack_from('<III', buf, off); off += 12
                vendor = buf[off:off+ns]; off += (ns+3) & ~3
                desc = buf[off:off+ds]; off += (ds+3) & ~3
                if vendor.rstrip(b'\0') == b'AMDGPU' and typ == 32:
                    for k in msgpack.unpackb(desc, raw=False)['amdhsa.kernels']:
                        kernels[k['.name']] = k
        if h[1] == 2:
            stringh = hdr[h[6]]
            st = d[stringh[4]:stringh[4]+stringh[5]]
            for off in range(0, len(buf), h[9]):
                n, info, other, idx, value, size = struct.unpack_from('<IBBHQQ', buf, off)
                if info & 15 == 2 and idx and idx < num:
                    sec = hdr[idx]
                    begin = sec[4] + value - sec[3]
                    symbols[cstr(st, n)] = (value, size, d[begin:begin+size])
    return sections, kernels, symbols


def inspect(path, arch, objdump, cache):
    sections, kernels, symbols = elf(path)
    dest = cache / arch / path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    asm = subprocess.check_output([str(objdump), '-d', '--no-show-raw-insn', '--mcpu='+arch, str(path)], text=True)
    dest.with_suffix('.disasm.txt').write_text(asm)
    instructions = []
    for line in asm.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+([a-zA-Z_][\w.]*)', line)
        if m:
            instructions.append((int(m[1], 16), m[2]))
        elif (m := re.match(r'^\s*([a-zA-Z_][\w.]*)\s.*//\s*([0-9A-Fa-f]+):', line)):
            instructions.append((int(m[2], 16), m[1]))
        elif re.match(r'^\s*[0-9a-f]+:.*<unknown>', line):
            raise RuntimeError(f'Unknown instruction: {path}: {line}')
    result = {}
    for name, meta in kernels.items():
        if name not in symbols:
            raise RuntimeError(f'Kernel without function symbol: {path}: {name}')
        addr, size, code = symbols[name]
        counts = collections.Counter(op for pc, op in instructions if addr <= pc < addr+size)
        result[name] = dict(bytes=size, code_sha256=hashlib.sha256(code).hexdigest(),
                            instructions=sum(counts.values()), opcodes=dict(counts), metadata=meta)
        if not counts:
            raise RuntimeError(f'No instructions: {path}: {name}')
    return sections, result


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('baseline', type=Path); p.add_argument('candidate', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--objdump', type=Path, default=Path('/home/lmxxf/work/llvm-build-dlss5-gfx12/bin/llvm-objdump'))
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    rows, modules, details = [], [], {}
    keys = ['.vgpr_count', '.sgpr_count', '.group_segment_fixed_size', '.private_segment_fixed_size', '.wavefront_size', '.kernarg_segment_size']
    for arch in ['gfx1201', 'gfx1200']:
        base = {f.name:f for f in (a.baseline/arch).glob('*.hsaco')}
        cand = {f.name:f for f in (a.candidate/arch).glob('*.hsaco')}
        if set(base) != set(cand) or len(base) != 30:
            raise RuntimeError(f'Expected matching 30 module sets: {arch}')
        for name in sorted(base):
            bs, bk = inspect(base[name], arch, a.objdump, a.out/'disassembly-baseline')
            cs, ck = inspect(cand[name], arch, a.objdump, a.out/'disassembly-candidate')
            if set(bk) != set(ck):
                raise RuntimeError(f'Kernel exports differ: {arch}/{name}')
            modules.append(dict(arch=arch,module=name,kernels=len(bk),
                                same_sections=[s for s in ['.text','.rodata','.note'] if bs.get(s)==cs.get(s)]))
            details[arch+'/'+name] = dict(baseline=bk,candidate=ck)
            for k in sorted(bk):
                b,c = bk[k],ck[k]
                row = dict(arch=arch,module=name,kernel=k,same_code=b['code_sha256']==c['code_sha256'],
                           baseline_instructions=b['instructions'], candidate_instructions=c['instructions'],
                           delta_instructions=c['instructions']-b['instructions'],
                           baseline_bytes=b['bytes'],candidate_bytes=c['bytes'])
                for key in keys:
                    row['baseline'+key] = b['metadata'].get(key)
                    row['candidate'+key] = c['metadata'].get(key)
                rows.append(row)
    with (a.out/'kernel-diff.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    summary=dict(modules=modules,total_kernels=len(rows),same_kernel_code=sum(r['same_code'] for r in rows),
                 differing_kernel_code=sum(not r['same_code'] for r in rows))
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (a.out/'kernel-details.json').write_text(json.dumps(details,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='modules'}))


if __name__=='__main__':
    main()

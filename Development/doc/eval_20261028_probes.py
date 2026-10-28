"""Reproducible ablation probe builder and active-kernel SASS/resource auditor for PTX V2.7 evaluation."""
from pathlib import Path
import sys, os, re, json, hashlib, ctypes, struct, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = Path('/home/lmxxf/work/DLSS5-RTX-3080-laptop/Development/ptx-patcher')
sys.path.insert(0, str(REPO))
import build_sm86_dlls as b
from pe_fatbins import assemble
from ptx_mapped import mapped_at

TMP = Path('/tmp/v27_eval_ortho')
TMP.mkdir(parents=True, exist_ok=True)
CUOBJDUMP = '/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'

v27_sel = json.loads((REPO / 'v27/selected.json').read_text())
p23_prof = json.loads((REPO / 'v23/profile.json').read_text())

# Exact 40 active launched kernels (38 in FB00..FB06, 1 in FB13, 1 in FB14)
ACTIVE_BY_FB = {}
for call in p23_prof['1280']['calls']:
    ACTIVE_BY_FB.setdefault(int(call['FB']), set()).add(call['name'])

v27_path = Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v27.dll')
v27_bytes = bytearray(v27_path.read_bytes())
assert hashlib.sha256(v27_bytes).hexdigest() == v27_sel['sha256']
v27_locs = b.dp.find_fatbins(v27_bytes)
v27_blobs = {i: bytes(v27_bytes[l.offset:l.offset+l.size]) for i, l in enumerate(v27_locs)}

raw_orig = bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes())
assert hashlib.sha256(raw_orig).hexdigest() == '2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f'
b.dp.strip_authenticode(raw_orig)
orig_locs = b.dp.find_fatbins(raw_orig)
b.dp.apply_host_patches(raw_orig, (b.dp.AMPERE,))

stock_cap = b.override_maxnreg

def make_override(fb):
    def override(text, limit):
        text, count = stock_cap(text, limit)
        if fb == 0:
            parts = re.split(r'(?=\.visible \.entry )', text)
            for idx, part in enumerate(parts):
                m = re.match(r'\.visible \.entry (\w+)', part)
                if m and m[1] in v27_sel['kernel_caps']:
                    parts[idx], _ = stock_cap(part, v27_sel['kernel_caps'][m[1]])
            text = ''.join(parts)
        return text, count
    return override

def render_probe(matches, packed_sources, *, mode):
    operands = list(dict.fromkeys(m[n] for m in matches for n in ('a0','a1','a2','a3','b0','b1')))
    mapped = mapped_at(packed_sources, matches[0].start())

    if mode in ('p1_zerodecode', 'p2_zerodecode_zeropack'):
        first_write = {}
        for i, m in enumerate(matches):
            for s in (m['d0'], m['d1']): first_write.setdefault(s, 2*i)
        last_read = {}
        for i, m in enumerate(matches):
            for r in set(m[n] for n in ('a0','a1','a2','a3','b0','b1')):
                if r in mapped:
                    for phase, s in enumerate(mapped[r][:2]):
                        last_read[s] = max(last_read.get(s, -1), 2*i + phase)
                else:
                    last_read[r] = max(last_read.get(r, -1), 2*i + 1)
        save_at = {s: first_write[s] for s, end in last_read.items() if s in first_write and first_write[s] < end}
        free = []; allocated = 0; body = []; saved = {}
        def alloc():
            nonlocal allocated
            if free: return free.pop()
            r = f'vlh_t{allocated}'; allocated += 1; return r
        for i, m in enumerate(matches):
            for phase in [0, 1]:
                step = 2*i + phase
                for source, at in save_at.items():
                    if at == step:
                        t = alloc(); saved[source] = t; body.append(f'mov.b32 {t}, {source};')
                def operand(r):
                    source = mapped[r][phase] if r in mapped else r
                    return saved.get(source, source)
                aa = [operand(m[n]) for n in ('a0','a1','a2','a3')]
                bb = [operand(m[n]) for n in ('b0','b1')]
                cc = [m['c0'], m['c1']] if phase == 0 else [m['d0'], m['d1']]
                body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
                for source in list(saved):
                    if last_read[source] == step: free.append(saved.pop(source))
        decl = ['{']
        if allocated: decl += ['.reg .b32 ' + ', '.join(f'vlh_t{i}' for i in range(allocated)) + ';']
        return '\n'.join(decl + body + ['}'])

    elif mode == 'p3_zerodecode_1xhmma':
        # Single-variable change relative to P1_ZeroDecodeOnly: keep SWAR pack intact, emit 1x HMMA.16816 per FP8 K32 site
        mapped_ops = [r for r in operands if r in mapped]
        body = []
        decl = ['{']
        if mapped_ops:
            decl.append('.reg .b32 ' + ', '.join(f'vlh_m{i}' for i in range(len(mapped_ops))) + ';')
        m_names = {}
        for idx, r in enumerate(mapped_ops):
            low, high, _ = mapped[r]
            t = f'vlh_m{idx}'
            m_names[r] = t
            body.append(f'lop3.b32 {t}, {low}, {high}, {low}, 0x96;')
        for i, m in enumerate(matches):
            def operand(r):
                return m_names[r] if r in mapped else r
            aa = [operand(m[n]) for n in ('a0','a1','a2','a3')]
            bb = [operand(m[n]) for n in ('b0','b1')]
            cc = [m['c0'], m['c1']]
            body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
        return '\n'.join(decl + body + ['}'])
    else:
        raise ValueError(mode)

def worker_probe(args):
    fb, blob, mode = args
    cache_dir = TMP / f'cache_{mode}'
    os.environ['DLSSNR_BUILD_CACHE'] = str(cache_dir)
    b.override_maxnreg = make_override(fb)

    import v26.codegen as v26c
    import v22.codegen as v22c
    orig_render = v26c.render
    orig_decl = v22c.declarations
    orig_pack = v22c.pack

    if mode != 'p0_zeropack':
        v26c.render = lambda matches, packed_sources, *, builder=None, audit=None: render_probe(matches, packed_sources, mode=mode)
    if mode in ('p0_zeropack', 'p2_zerodecode_zeropack'):
        v22c.declarations = lambda: []
        v22c.pack = lambda src, dst: [f'cvt.u16.u32 {dst}, {src};']
    try:
        cap = v27_sel['base_caps'].get(str(fb))
        return b.worker_compile_fatbin((fb, blob, True, True, 'multidef', False, 'lowhigh', cap, 'swar', 'mbarrier', 'lowhigh8', 8))
    finally:
        v26c.render = orig_render
        v22c.declarations = orig_decl
        v22c.pack = orig_pack

def extract_v27_cubins():
    v27_cache = TMP / 'cache_v27'
    v27_cache.mkdir(parents=True, exist_ok=True)
    libzstd = ctypes.CDLL('libzstd.so.1')
    libzstd.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    libzstd.ZSTD_decompress.restype = ctypes.c_size_t
    for i in range(7):
        fb_blob = v27_bytes[v27_locs[i].offset:v27_locs[i].offset+v27_locs[i].size]
        rec = [r for r in b.dp.parse_fatbin_records(fb_blob) if r.kind == 2][0]
        hdr = fb_blob[rec.offset:rec.offset+rec.header_size]
        pad_sz, comp_sz = struct.unpack_from('<QI', hdr, 0x08)
        uncomp_sz = struct.unpack_from('<Q', hdr, 0x38)[0]
        payload = bytes(fb_blob[rec.offset+rec.header_size:rec.offset+rec.header_size+comp_sz])
        dst = ctypes.create_string_buffer(uncomp_sz)
        ret = libzstd.ZSTD_decompress(dst, uncomp_sz, payload, len(payload))
        assert ret == uncomp_sz
        (v27_cache / f'fatbin{i:02d}.cubin').write_bytes(dst.raw)

def audit_active_38():
    extract_v27_cubins()
    modes = ['v27', 'p0_zeropack', 'p1_zerodecode', 'p2_zerodecode_zeropack', 'p3_zerodecode_1xhmma']
    out = {'active_kernel_count_fb0_to_6': sum(len(ACTIVE_BY_FB[fb]) for fb in range(7)), 'modes': {}}
    for mode in modes:
        cdir = TMP / f'cache_{mode}'
        by_fb = {}
        by_kernel = {}
        tot = {'INSN':0, 'HMMA':0, 'PRMT':0, 'LDG':0, 'LDS':0, 'STS':0, 'LDGSTS':0, 'STL':0, 'LDL':0}
        for fb in range(7):
            cubin = cdir / f'fatbin{fb:02d}.cubin'
            sass = subprocess.check_output([CUOBJDUMP, '--dump-sass', str(cubin)], text=True)
            res = subprocess.check_output([CUOBJDUMP, '--dump-resource-usage', str(cubin)], text=True)
            k_res = {}
            cur_k = None
            for line in res.splitlines():
                m = re.search(r'Function (\w+):', line)
                if m: cur_k = m.group(1)
                elif cur_k in ACTIVE_BY_FB[fb] and 'REG:' in line:
                    mr = re.search(r'REG:(\d+)\s+STACK:(\d+)\s+SHARED:(\d+)', line)
                    if mr:
                        k_res[cur_k] = {'REG': int(mr.group(1)), 'STACK': int(mr.group(2)), 'SHARED': int(mr.group(3))}
            fb_counts = {'INSN':0, 'HMMA':0, 'PRMT':0, 'LDG':0, 'LDS':0, 'STS':0, 'LDGSTS':0, 'STL':0, 'LDL':0,
                         'MIN_REG': min(v['REG'] for v in k_res.values()),
                         'MAX_REG': max(v['REG'] for v in k_res.values()),
                         'MAX_STACK': max(v['STACK'] for v in k_res.values())}
            for part in re.split(r'Function : ', sass)[1:]:
                kname = part.splitlines()[0].strip()
                if kname not in ACTIVE_BY_FB[fb]: continue
                kc = {'FB': fb, **k_res[kname], 'INSN':0, 'HMMA':0, 'PRMT':0, 'LDG':0, 'LDS':0, 'STS':0, 'LDGSTS':0, 'STL':0, 'LDL':0}
                for line in part.splitlines()[1:]:
                    m_op = re.match(r'^\s*/\*[0-9a-f]+\*/\s+(?:@[!P\d]+\s+)?([A-Z0-9_.]+)', line)
                    if not m_op: continue
                    op = m_op.group(1)
                    if op == 'NOP': continue
                    kc['INSN'] += 1
                    if op.startswith('HMMA.'): kc['HMMA'] += 1
                    elif op.startswith('PRMT'): kc['PRMT'] += 1
                    elif op.startswith('LDGSTS'): kc['LDGSTS'] += 1
                    elif op.startswith('LDG'): kc['LDG'] += 1
                    elif op.startswith('LDS'): kc['LDS'] += 1
                    elif op.startswith('STS'): kc['STS'] += 1
                    elif op.startswith('STL'): kc['STL'] += 1
                    elif op.startswith('LDL'): kc['LDL'] += 1
                by_kernel[kname] = kc
                for k in tot:
                    fb_counts[k] += kc[k]
                    tot[k] += kc[k]
            by_fb[str(fb)] = fb_counts
        out['modes'][mode] = {'TOTAL_38_ACTIVE': tot, 'by_FB': by_fb, 'by_kernel': by_kernel}
        print(f'=== {mode} (38 active launched kernels in FB00..FB06) ===')
        print('  TOTAL:', tot)
        for fb in range(7):
            c = by_fb[str(fb)]
            print(f'  FB0{fb}: INSN={c["INSN"]:6d} HMMA={c["HMMA"]:5d} PRMT={c["PRMT"]:5d} LDG={c["LDG"]:4d} LDS={c["LDS"]:4d} STL/LDL={c["STL"]}/{c["LDL"]} REG={c["MIN_REG"]}..{c["MAX_REG"]} MAX_STACK={c["MAX_STACK"]}')
    return out

if __name__ == '__main__':
    dll_meta = {'v27': {'path': str(v27_path), 'sha256': v27_sel['sha256']}}
    for mode in ['p0_zeropack', 'p1_zerodecode', 'p2_zerodecode_zeropack', 'p3_zerodecode_1xhmma']:
        out_dll = Path(f'/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_{mode}.dll')
        if not out_dll.exists() or not (TMP / f'cache_{mode}/fatbin06.cubin').exists():
            print(f'Building {mode} ...', flush=True)
            blobs = dict(v27_blobs)
            tasks = [(i, bytes(raw_orig[orig_locs[i].offset:orig_locs[i].offset+orig_locs[i].size]), mode) for i in range(7)]
            with ProcessPoolExecutor(max_workers=3) as pool:
                for fut in as_completed([pool.submit(worker_probe, t) for t in tasks]):
                    i, blob, msg = fut.result()
                    assert 'ELF O4' in msg, (mode, i, msg)
                    blobs[i] = blob
            data = bytearray(raw_orig)
            data, manifest = assemble(data, orig_locs, blobs, b.dp)
            b.fast_update_pe_checksum(data)
            out_dll.write_bytes(data)
        data = out_dll.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        dll_meta[mode] = {'path': str(out_dll), 'sha256': sha, 'bytes': len(data)}
        print(f'  -> {out_dll.name} SHA256={sha}', flush=True)
    audit = audit_active_38()
    audit['dll_meta'] = dll_meta
    (TMP / 'active38_sass_audit.json').write_text(json.dumps(audit, indent=2))



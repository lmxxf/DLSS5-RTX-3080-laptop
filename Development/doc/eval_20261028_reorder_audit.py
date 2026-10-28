"""Strict hazard-checked MMA-run topological reordering audit on top of PTX V2.9_fast (SHA 55b51876)."""
from pathlib import Path
import sys, os, re, json, hashlib, ctypes, struct, subprocess, collections
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = Path('/home/lmxxf/work/DLSS5-RTX-3080-laptop/Development/ptx-patcher')
sys.path.insert(0, str(REPO))
import build_sm86_dlls as b
import v26.codegen as v26c
import v22.codegen as v22c
import v29.codegen as v29_gen
from ptx_mapped import mapped_at

CUOBJDUMP = '/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
DOC = Path('/home/lmxxf/work/DLSS5-RTX-3080-laptop/Development/doc')
TMP = Path('/tmp/v29_reorder_audit')
TMP.mkdir(parents=True, exist_ok=True)

v27_sel = json.loads((REPO / 'v27/selected.json').read_text())
p23 = json.loads((REPO / 'v23/profile.json').read_text())
ACTIVE_BY_FB = {int(c['FB']): set() for c in p23['1280']['calls']}
for c in p23['1280']['calls']:
    ACTIVE_BY_FB[int(c['FB'])].add(c['name'])

raw_orig = bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes())
assert hashlib.sha256(raw_orig).hexdigest() == '2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f'
b.dp.strip_authenticode(raw_orig)
orig_locs = b.dp.find_fatbins(raw_orig)
b.dp.apply_host_patches(raw_orig, (b.dp.AMPERE,))
stock_cap = b.override_maxnreg

def expanded_rw(m, mapped):
    writes = {m['d0'], m['d1']}
    reads = {m['c0'], m['c1']}
    for k in ('a0', 'a1', 'a2', 'a3', 'b0', 'b1'):
        r = m[k]
        reads.add(r)
        if r in mapped:
            reads.add(mapped[r][0])
            reads.add(mapped[r][1])
    return reads, writes

def has_hazard(matches, order, mapped):
    """Check RAW, WAR, WAW hazards across both literal PTX operands and implicit mapped (low, high) sources."""
    pos = {orig_idx: new_idx for new_idx, orig_idx in enumerate(order)}
    rws = [expanded_rw(m, mapped) for m in matches]
    for i in range(len(matches)):
        ri, wi = rws[i]
        for j in range(i + 1, len(matches)):
            rj, wj = rws[j]
            if (wi & (wj | rj)) or (wj & ri):
                if pos[i] > pos[j]:
                    return True
    return False

def get_chains(matches, mapped):
    n = len(matches)
    rws = [expanded_rw(m, mapped) for m in matches]
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in range(n):
        ri, wi = rws[i]
        for j in range(i + 1, len(matches)):
            rj, wj = rws[j]
            if (wi & (wj | rj)) or (wj & ri):
                pi, pj = find(i), find(j)
                if pi != pj:
                    parent[max(pi, pj)] = min(pi, pj)
    comps = collections.defaultdict(list)
    for i in range(n):
        comps[find(i)].append(i)
    return list(comps.values())

def render_with_fixed_mapped(matches, mapped, *, audit=None):
    """Exact v26.codegen.render logic but with pre-resolved `mapped` from original run start."""
    operands = list(dict.fromkeys(m[n] for m in matches for n in ('a0','a1','a2','a3','b0','b1')))
    first = {r: min(i for i, m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
    last  = {r: max(i for i, m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
    first_write = {}
    for i, m in enumerate(matches):
        for s in (m['d0'], m['d1']):
            first_write.setdefault(s, 2*i)
    last_read = {}
    for i, m in enumerate(matches):
        for r in set(m[n] for n in ('a0','a1','a2','a3','b0','b1')):
            if r in mapped:
                for phase, s in enumerate(mapped[r][:2]):
                    last_read[s] = max(last_read.get(s, -1), 2*i + phase)
    save_at = {s: first_write[s] for s, end in last_read.items() if s in first_write and first_write[s] < end}
    encoded = [r for r in operands if r not in mapped]
    when = {r: min(first[r], first_write.get(r, 2*first[r]) // 2) for r in encoded}
    free = []; allocated = 0; body = []; decoded = {}; saved = {}; backup_moves = 0
    def alloc():
        nonlocal allocated
        if free: return free.pop()
        r = f'vlh_t{allocated}'; allocated += 1; return r
    for i, m in enumerate(matches):
        for r in encoded:
            if when[r] == i:
                pair = (alloc(), alloc()); decoded[r] = pair; body.extend(v26c.decode(r, *pair))
        for phase in [0, 1]:
            step = 2*i + phase
            for source, at in save_at.items():
                if at == step:
                    tmp = alloc(); saved[source] = tmp; body.append(f'mov.b32 {tmp}, {source};'); backup_moves += 1
            def operand(r):
                if r not in mapped: return decoded[r][phase]
                source = mapped[r][phase]; return saved.get(source, source)
            aa = [operand(m[n]) for n in ('a0','a1','a2','a3')]
            bb = [operand(m[n]) for n in ('b0','b1')]
            cc = [m['c0'], m['c1']] if phase == 0 else [m['d0'], m['d1']]
            body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
            for source in list(saved):
                if last_read[source] == step: free.append(saved.pop(source))
        for r in list(decoded):
            if last[r] == i: free.extend(decoded.pop(r))
    decl = ['{']
    if allocated: decl += ['.reg .b32 ' + ', '.join(f'vlh_t{i}' for i in range(allocated)) + ';']
    if encoded: decl += ['.reg .b32 dlssnr_fp8_scale;', 'mov.b32 dlssnr_fp8_scale, 0x5c005c00;']
    if audit is not None:
        audit.append({
            'mma_sites': len(matches),
            'mapped_operands': sum(r in mapped for r in operands),
            'encoded_operands': len(encoded),
            'temporary_b32_peak': allocated,
            'backup_moves': backup_moves,
            'phase0_clobber_sources': sorted(save_at)
        })
    return '\n'.join(decl + body + ['}'])

def render_reordered(matches, packed_sources, *, builder=None, audit=None):
    orig_start = matches[0].start()
    mapped = mapped_at(packed_sources, orig_start)
    n = len(matches)
    chains = get_chains(matches, mapped)
    max_len = max(len(ch) for ch in chains)
    by_step_b, by_step_a = [], []
    for step in range(max_len):
        step_ins = [ch[step] for ch in chains if step < len(ch)]
        first_b = {}
        for i in step_ins: first_b.setdefault((matches[i]['b0'], matches[i]['b1']), i)
        by_step_b.extend(sorted(step_ins, key=lambda i: (first_b[(matches[i]['b0'], matches[i]['b1'])], i)))
        first_a = {}
        for i in step_ins: first_a.setdefault((matches[i]['a0'], matches[i]['a1'], matches[i]['a2'], matches[i]['a3']), i)
        by_step_a.extend(sorted(step_ins, key=lambda i: (first_a[(matches[i]['a0'], matches[i]['a1'], matches[i]['a2'], matches[i]['a3'])], i)))

    a_orig = []
    out_orig = render_with_fixed_mapped(matches, mapped, audit=a_orig)
    best_out = out_orig
    best_audit = a_orig[0]
    best_order = list(range(n))

    for tag, order in [('by_step_b', by_step_b), ('by_step_a', by_step_a)]:
        if len(order) == n and not has_hazard(matches, order, mapped):
            cand = [matches[i] for i in order]
            ac = []
            out_c = render_with_fixed_mapped(cand, mapped, audit=ac)
            # Require identical mapped/encoded counts and backup_moves == 0
            assert ac[0]['mapped_operands'] == a_orig[0]['mapped_operands']
            assert ac[0]['encoded_operands'] == a_orig[0]['encoded_operands']
            assert ac[0]['backup_moves'] == a_orig[0]['backup_moves'] == 0
            if ac[0]['temporary_b32_peak'] < best_audit['temporary_b32_peak']:
                best_audit = ac[0]
                best_out = out_c
                best_order = order
    if audit is not None:
        audit.append({**best_audit, 'orig_temporary_b32_peak': a_orig[0]['temporary_b32_peak'], 'reordered': best_order != list(range(n))})
    return best_out

def worker_compile(fb):
    cdir = TMP / 'cache_reordered'
    os.environ['DLSSNR_BUILD_CACHE'] = str(cdir)
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
    b.override_maxnreg = override
    v26c.render = render_reordered
    v29_gen.MODE = 'fast'
    v22c.declarations = v29_gen.declarations
    v22c.pack = v29_gen.pack
    cap = v27_sel['base_caps'].get(str(fb))
    blob = bytes(raw_orig[orig_locs[fb].offset:orig_locs[fb].offset+orig_locs[fb].size])
    b.worker_compile_fatbin((fb, blob, True, True, 'multidef', False, 'lowhigh', cap, 'swar', 'mbarrier', 'lowhigh8', 8))
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
            if mr: k_res[cur_k] = {'REG': int(mr.group(1)), 'STACK': int(mr.group(2)), 'SHARED': int(mr.group(3))}
    by_k = {}
    for part in re.split(r'Function : ', sass)[1:]:
        kname = part.splitlines()[0].strip()
        if kname not in ACTIVE_BY_FB[fb]: continue
        kc = {'FB': fb, **k_res[kname], 'INSN_NONOP':0, 'INSN_WITH_NOP':0, 'HMMA':0, 'PRMT':0, 'STL':0, 'LDL':0}
        for line in part.splitlines()[1:]:
            m_op = re.match(r'^\s*/\*[0-9a-f]+\*/\s+(?:@[!P\d]+\s+)?([A-Z0-9_.]+)', line)
            if not m_op: continue
            op = m_op.group(1)
            kc['INSN_WITH_NOP'] += 1
            if op == 'NOP': continue
            kc['INSN_NONOP'] += 1
            if op.startswith('HMMA.'): kc['HMMA'] += 1
            elif op.startswith('PRMT'): kc['PRMT'] += 1
            elif op.startswith('STL'): kc['STL'] += 1
            elif op.startswith('LDL'): kc['LDL'] += 1
        by_k[kname] = kc
    return fb, by_k

if __name__ == '__main__':
    d1506 = json.loads((DOC / '性能评估20261028-1506-实验数据.json').read_text())
    v29_k = d1506['active38_sass_and_resource_audit']['modes']['v29_fast']['by_kernel']
    v27_k = d1506['active38_sass_and_resource_audit']['modes']['v27']['by_kernel']

    reord_k = {}
    with ProcessPoolExecutor(max_workers=3) as pool:
        for fut in as_completed([pool.submit(worker_compile, fb) for fb in range(7)]):
            fb, by_k = fut.result()
            reord_k.update(by_k)

    print('=== EXACT PER-KERNEL DIFF: V2.9_fast (SHA 55b51876) -> V2.9_fast + Topological Reorder ===')
    diffs = {}
    for k in sorted(reord_k):
        a = v29_k[k]
        r = reord_k[k]
        if (a['REG'], a['STACK'], a['STL'], a['LDL'], a['INSN_NONOP']) != (r['REG'], r['STACK'], r['STL'], r['LDL'], r['INSN_NONOP']):
            diffs[k] = {'v27': v27_k[k], 'v29_fast': a, 'v29_reordered': r}
            print(f'  FB0{r["FB"]} {k:<52}: REG {a["REG"]:3d}->{r["REG"]:3d} ({r["REG"]-a["REG"]:+3d}) | STACK {a["STACK"]:3d}->{r["STACK"]:3d}B ({r["STACK"]-a["STACK"]:+3d}B) | STL/LDL {a["STL"]}/{a["LDL"]}->{r["STL"]}/{r["LDL"]} | INSN {a["INSN_NONOP"]}->{r["INSN_NONOP"]} ({r["INSN_NONOP"]-a["INSN_NONOP"]:+d})')

    d1506['v29_reordered_static_audit'] = {'by_kernel': reord_k, 'changed_kernels_vs_v29_fast': diffs}
    (DOC / '性能评估20261028-1506-实验数据.json').write_text(json.dumps(d1506, indent=2) + '\n')
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)

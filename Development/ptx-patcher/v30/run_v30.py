"""PTX V3.0: Hazard-checked K-Step De-interleaved B/A-Stationary MMA Reordering on top of V2.9_fast."""
from pathlib import Path
import sys, os, re, json, hashlib, subprocess, datetime, statistics as st, numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

P = Path(__file__).resolve().parent
REPO = P.parent
DOC = REPO.parent / 'doc'
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(DOC))

import build_sm86_dlls as b
from pe_fatbins import assemble
import eval_20261028_reorder_audit as ra
import v26.codegen as v26c
import v22.codegen as v22c
import v29.codegen as v29_gen

ROOT = Path('/mnt/c/DLSS5-5090-dll')
CORE = r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
BENCH_EXE = str(ROOT / 'nvngx.dll_runner/bench_sky.exe')

v27_sel = json.loads((REPO / 'v27/selected.json').read_text())
v29_path = ROOT / 'nvngx_dlssnr_sm86_v29_fast.dll'
v29_bytes = bytearray(v29_path.read_bytes())
v29_sha = hashlib.sha256(v29_bytes).hexdigest()
assert v29_sha == '55b518762bbe4d43fbe71f838352e23584d719736d86dd45437f4f50fc135f5c'
v29_locs = b.dp.find_fatbins(v29_bytes)
v29_blobs = {i: bytes(v29_bytes[l.offset:l.offset+l.size]) for i, l in enumerate(v29_locs)}

raw_orig = bytearray((ROOT / 'nvngx_dlssnr.dll').read_bytes())
b.dp.strip_authenticode(raw_orig)
orig_locs = b.dp.find_fatbins(raw_orig)
b.dp.apply_host_patches(raw_orig, (b.dp.AMPERE,))
stock_cap = b.override_maxnreg

def worker_compile(fb):
    cdir = P / 'artifacts/reordered'
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
    v26c.render = ra.render_reordered
    v29_gen.MODE = 'fast'
    v22c.declarations = v29_gen.declarations
    v22c.pack = v29_gen.pack
    cap = v27_sel['base_caps'].get(str(fb))
    blob = bytes(raw_orig[orig_locs[fb].offset:orig_locs[fb].offset+orig_locs[fb].size])
    return b.worker_compile_fatbin((fb, blob, True, True, 'multidef', False, 'lowhigh', cap, 'swar', 'mbarrier', 'lowhigh8', 8))

if __name__ == '__main__':
    print('=== 1. Building reordered fatbins FB00..FB06 ===', flush=True)
    reord_blobs = {}
    with ProcessPoolExecutor(max_workers=3) as pool:
        for fut in as_completed([pool.submit(worker_compile, fb) for fb in range(7)]):
            i, blob, msg = fut.result()
            assert 'ELF O4' in msg, (i, msg)
            reord_blobs[i] = blob
            print(f'  FB{i:02d}: {msg}', flush=True)

    candidates = {}
    for cname, target_fbs in [('v30_all', {0,1,2,3,4,5,6}), ('v30_fb14', {1,4})]:
        blobs = {i: (reord_blobs[i] if i in target_fbs else v29_blobs[i]) for i in range(15)}
        data = bytearray(raw_orig)
        data, manifest = assemble(data, orig_locs, blobs, b.dp)
        b.fast_update_pe_checksum(data)
        out_dll = ROOT / f'nvngx_dlssnr_sm86_{cname}.dll'
        out_dll.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        candidates[cname] = {'path': str(out_dll), 'sha256': sha, 'reordered_fbs': sorted(target_fbs), 'bytes': len(data)}
        print(f'Saved {cname}: {out_dll} SHA256={sha}', flush=True)

    (P / 'candidates.json').write_text(json.dumps(candidates, indent=2) + '\n')

    dll_map = {'baseline': str(v29_path)} | {k: v['path'] for k, v in candidates.items()}
    sha_map = {'baseline': v29_sha} | {k: v['sha256'] for k, v in candidates.items()}

    outdir = ROOT / 'ptx-v30-bench'
    outdir.mkdir(exist_ok=True)
    bench_rows = []

    def run_one(tag, ver, w, warm=50, it=80):
        h = {1280: 720, 1600: 900, 1920: 1080}[w]
        out = outdir / f'{tag}-{ver}-{w}.rgb32'
        args = [BENCH_EXE, CORE, dll_map[ver].replace('/mnt/c/', 'C:/'), str(w), str(h), '2', str(warm), str(it), str(out).replace('/mnt/c/', 'C:/')] + (['sky'] if w == 1280 else [])
        t0 = datetime.datetime.now().isoformat()
        r = subprocess.run(args, capture_output=True, text=True, timeout=90)
        t1 = datetime.datetime.now().isoformat()
        assert r.returncode == 0, (tag, ver, w, r.stdout, r.stderr)
        summary = [l for l in r.stdout.splitlines() if l.startswith('SUMMARY')][0]
        metrics = {k: float(v) for k, v in re.findall(r'(\w+)=([-+\d.eE]+)', summary)}
        assert metrics.get('nonfinite') == 0, summary
        a = np.fromfile(out, np.float32)
        assert len(a) == w * h * 3 and np.isfinite(a).all()
        gold = outdir / f'gold-{warm}-{it}-{w}.rgb32'
        if not gold.exists():
            assert ver == 'baseline'
            out.replace(gold)
        b_arr = np.fromfile(gold, np.float32)
        bits = int(np.count_nonzero(a.view(np.uint32) != b_arr.view(np.uint32)))
        maxabs = float(np.max(np.abs(a.astype(np.float64) - b_arr)))
        if out.exists():
            out.unlink()
        assert bits == 0 and maxabs == 0.0, f'Bitdiff failure on {ver} {w}: bits={bits}, maxabs={maxabs}'
        row = {
            'name': tag, 'variant': ver, 'dll_sha256': sha_map[ver], 'width': w, 'height': h,
            'warmup': warm, 'iterations': it, 'begin': t0, 'end': t1,
            'metrics': metrics, 'bitdiff_vs_v29_fast': bits, 'maxabs_vs_v29_fast': maxabs,
            'summary_line': summary
        }
        bench_rows.append(row)
        print(f'  {tag:<26} {ver:<10} w={w}: median={metrics["gpu_median_ms"]:.4f} ms, bitdiff={bits}', flush=True)

    print('=== 2. Smoke 1/1 0-bit check at 720p ===', flush=True)
    for v in ['baseline', 'v30_all', 'v30_fb14']:
        run_one('smoke', v, 1280, 1, 1)

    print('=== 3. Paired 50/80 ABBA / BAAB sweeps across 720p, 900p, 1080p ===', flush=True)
    for direction, widths in [('forward', [1280, 1600, 1920]), ('reverse', [1920, 1600, 1280])]:
        for w in widths:
            for cand in ['v30_all', 'v30_fb14']:
                order = ['baseline', cand, cand, 'baseline'] if direction == 'forward' else [cand, 'baseline', 'baseline', cand]
                for j, ver in enumerate(order):
                    run_one(f'{direction}-{cand}-{j}', ver, w, 50, 80)

    (P / 'bench.json').write_text(json.dumps(bench_rows, indent=2) + '\n')

    # Clean up gold rgb32 and artifacts
    import shutil
    shutil.rmtree(outdir, ignore_errors=True)
    shutil.rmtree(P / 'artifacts', ignore_errors=True)

    # Summarize paired results
    summary_out = {}
    print('\n=== 4. FINAL V3.0 PAIRED SUMMARY vs V2.9_fast ===', flush=True)
    for cand in ['v30_all', 'v30_fb14']:
        summary_out[cand] = {}
        for w in [1280, 1600, 1920]:
            fwd_b = st.mean(r['metrics']['gpu_median_ms'] for r in bench_rows if r['width']==w and r['name'].startswith(f'forward-{cand}-') and r['variant']=='baseline')
            fwd_c = st.mean(r['metrics']['gpu_median_ms'] for r in bench_rows if r['width']==w and r['name'].startswith(f'forward-{cand}-') and r['variant']==cand)
            rev_b = st.mean(r['metrics']['gpu_median_ms'] for r in bench_rows if r['width']==w and r['name'].startswith(f'reverse-{cand}-') and r['variant']=='baseline')
            rev_c = st.mean(r['metrics']['gpu_median_ms'] for r in bench_rows if r['width']==w and r['name'].startswith(f'reverse-{cand}-') and r['variant']==cand)
            b_mean = (fwd_b + rev_b) / 2
            c_mean = (fwd_c + rev_c) / 2
            pct = (b_mean - c_mean) / b_mean * 100
            pct_f = (fwd_b - fwd_c) / fwd_b * 100
            pct_r = (rev_b - rev_c) / rev_b * 100
            summary_out[cand][str(w)] = {
                'v29_fast_ms': round(b_mean, 6), 'cand_ms': round(c_mean, 6),
                'saving_ms': round(b_mean - c_mean, 6), 'saving_pct': round(pct, 4),
                'forward_saving_pct': round(pct_f, 4), 'reverse_saving_pct': round(pct_r, 4),
                'all_runs_0_bitdiff': True
            }
            print(f'  {cand:<10} w={w}: V29_fast={b_mean:.5f} -> {cand}={c_mean:.5f} ms | diff={b_mean-c_mean:+.5f} ms ({pct:+.3f}%: fwd {pct_f:+.3f}% / rev {pct_r:+.3f}%) | 0-bitdiff PASS', flush=True)

    (P / 'bench-summary.json').write_text(json.dumps(summary_out, indent=2) + '\n')

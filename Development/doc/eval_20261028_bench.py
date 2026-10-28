"""Run orthogonal 5-way ablation benchmark (V2.7, P0_ZeroPack, P1_ZeroDecode, P2_Both, P3_ZeroDecode_1xHMMA)."""
from pathlib import Path
import subprocess, os, re, json, statistics as st, collections

REPO = Path('/home/lmxxf/work/DLSS5-RTX-3080-laptop/Development/ptx-patcher')
TMP = Path('/tmp/v27_eval_ortho')
ROOT = Path('/mnt/c/DLSS5-5090-dll')
CORE = r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
BENCH_EXE = str(ROOT / 'nvngx.dll_runner/bench_sky.exe')
PROF_EXE = str(ROOT / 'nvngx.dll_runner/bench_profile.exe')

if not Path(PROF_EXE).exists():
    subprocess.run(['python3', str(REPO / 'v23/build_profile.py')], check=True)

p23_prof = json.loads((REPO / 'v23/profile.json').read_text())
fb_map = {c['name']: int(c['FB']) for c in p23_prof['1280']['calls']}

DLLS = {
    'v27': str(ROOT / 'nvngx_dlssnr_sm86_v27.dll'),
    'p0':  str(ROOT / 'nvngx_dlssnr_sm86_p0_zeropack.dll'),
    'p1':  str(ROOT / 'nvngx_dlssnr_sm86_p1_zerodecode.dll'),
    'p2':  str(ROOT / 'nvngx_dlssnr_sm86_p2_zerodecode_zeropack.dll'),
    'p3':  str(ROOT / 'nvngx_dlssnr_sm86_p3_zerodecode_1xhmma.dll'),
}

ORDER_FWD = ['v27', 'p0', 'p1', 'p2', 'p3']
ORDER_REV = ['p3', 'p2', 'p1', 'p0', 'v27']

print('=== 1. UNINSTRUMENTED 5-WAY ORTHOGONAL SWEEPS (50/80) ===', flush=True)
whole_records = []
for w, h in [(1280, 720), (1600, 900), (1920, 1080)]:
    for pass_idx, order in enumerate([ORDER_FWD, ORDER_REV, ORDER_FWD, ORDER_REV]):
        for ver in order:
            out = ROOT / f'ortho-whole-{ver}-{w}.rgb32'
            args = [BENCH_EXE, CORE, DLLS[ver].replace('/mnt/c/', 'C:/'), str(w), str(h), '2', '50', '80', str(out).replace('/mnt/c/', 'C:/')] + (['sky'] if w == 1280 else [])
            r = subprocess.run(args, capture_output=True, text=True, timeout=90)
            assert r.returncode == 0, (ver, w, r.stdout, r.stderr)
            out.unlink(missing_ok=True)
            m = re.search(r'gpu_median_ms=([\d.]+)\s+gpu_mean_ms=([\d.]+)\s+gpu_min_ms=([\d.]+)', r.stdout)
            assert m, r.stdout
            med_ms, mean_ms, min_ms = map(float, m.groups())
            whole_records.append({'ver': ver, 'width': w, 'pass': pass_idx, 'median_ms': med_ms, 'mean_ms': mean_ms, 'min_ms': min_ms})
        print(f'  Width {w} pass {pass_idx}: ' + ', '.join(f'{v}={next(x["median_ms"] for x in reversed(whole_records) if x["ver"]==v and x["width"]==w):.4f}' for v in ORDER_FWD), flush=True)

(TMP / 'ortho_whole.json').write_text(json.dumps(whole_records, indent=2))

print('=== 2. NVAPI PER-KERNEL 5-WAY SWEEPS (50/20) ===', flush=True)
prof_records = []
for w, h in [(1280, 720), (1600, 900), (1920, 1080)]:
    for pass_idx, order in enumerate([ORDER_FWD, ORDER_REV]):
        for ver in order:
            tag = f'{ver}-p{pass_idx}-{w}'
            trace = ROOT / f'ortho-{tag}.csv'
            out = ROOT / f'ortho-{tag}.rgb32'
            env = os.environ.copy()
            env['V23_TRACE'] = str(trace).replace('/mnt/c/', 'C:/')
            env['V23_EVENTS'] = '1'
            env['WSLENV'] = env.get('WSLENV', '') + ':V23_TRACE:V23_EVENTS'
            args = [PROF_EXE, CORE, DLLS[ver].replace('/mnt/c/', 'C:/'), str(w), str(h), '2', '50', '20', str(out).replace('/mnt/c/', 'C:/')] + (['sky'] if w == 1280 else [])
            r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=90)
            assert r.returncode == 0, (tag, r.returncode)
            csv_text = trace.read_text()
            trace.unlink(missing_ok=True)
            out.unlink(missing_ok=True)

            rows = []
            for l in csv_text.splitlines():
                if not l.startswith('KERNEL,'): continue
                x = l.split(',')
                frame = int(x[1])
                if frame < 50: continue
                rows.append({'frame': frame, 'call': int(x[2]), 'name': x[4], 'FB': fb_map.get(x[4], -1), 'gpu_ms': float(x[12]), 'start': int(x[13]), 'end': int(x[14])})
            frames = collections.defaultdict(list)
            for row in rows: frames[row['frame']].append(row)
            by_fb = {}
            for fb_id in sorted(set(row['FB'] for row in rows)):
                samples = [sum(row['gpu_ms'] for row in rs if row['FB'] == fb_id) for rs in frames.values()]
                by_fb[str(fb_id)] = {'mean_ms': st.mean(samples), 'median_ms': st.median(samples)}
            sum_ms = st.mean(sum(row['gpu_ms'] for row in rs) for rs in frames.values())
            prof_records.append({'ver': ver, 'pass': pass_idx, 'width': w, 'sum_ms': sum_ms, 'by_FB': by_fb})
        print(f'  NVAPI Width {w} pass {pass_idx}: ' + ', '.join(f'{v}={next(x["sum_ms"] for x in reversed(prof_records) if x["ver"]==v and x["width"]==w):.4f}' for v in ORDER_FWD), flush=True)

(TMP / 'ortho_nvapi.json').write_text(json.dumps(prof_records, indent=2))
print('ALL ORTHOGONAL ABLATION RUNS DONE', flush=True)

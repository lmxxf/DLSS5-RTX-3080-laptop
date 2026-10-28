"""Run 5-way evaluation benchmark for PTX V2.9_fast (V2.7, V2.9_fast, P0_ZeroPack, P1_V29_ZeroDecode, P2_Both)."""
from pathlib import Path
import subprocess, os, re, json, hashlib, statistics as st, collections, datetime

REPO = Path('/home/lmxxf/work/DLSS5-RTX-3080-laptop/Development/ptx-patcher')
TMP = Path('/tmp/v29_eval_1506')
ROOT = Path('/mnt/c/DLSS5-5090-dll')
CORE = r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
BENCH_EXE = str(ROOT / 'nvngx.dll_runner/bench_sky.exe')
PROF_EXE = str(ROOT / 'nvngx.dll_runner/bench_profile.exe')

if not Path(PROF_EXE).exists():
    subprocess.run(['python3', str(REPO / 'v23/build_profile.py')], check=True)

p23_prof = json.loads((REPO / 'v23/profile.json').read_text())
fb_map = {c['name']: int(c['FB']) for c in p23_prof['1280']['calls']}

DLLS = {
    'v27':      str(ROOT / 'nvngx_dlssnr_sm86_v27.dll'),
    'v29_fast': str(ROOT / 'nvngx_dlssnr_sm86_v29_fast.dll'),
    'p0':       str(ROOT / 'nvngx_dlssnr_sm86_p0_zeropack.dll'),
    'p1_v29':   str(ROOT / 'nvngx_dlssnr_sm86_p1_v29_zerodecode.dll'),
    'p2':       str(ROOT / 'nvngx_dlssnr_sm86_p2_zerodecode_zeropack.dll'),
}

DLL_SHAS = {k: hashlib.sha256(Path(v).read_bytes()).hexdigest() for k, v in DLLS.items()}

ORDER_FWD = ['v27', 'v29_fast', 'p0', 'p1_v29', 'p2']
ORDER_REV = ['p2', 'p1_v29', 'p0', 'v29_fast', 'v27']

telem_file = TMP / 'telemetry_1506.csv'
telem_proc = subprocess.Popen(
    ['nvidia-smi', '--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.current.sm,clocks.current.memory,clocks_throttle_reasons.sw_thermal_slowdown,utilization.gpu', '--format=csv', '-lms', '250'],
    stdout=telem_file.open('w'), stderr=subprocess.DEVNULL
)

try:
    print('=== 1. UNINSTRUMENTED 5-WAY SWEEPS (50/80) ===', flush=True)
    whole_records = []
    for w, h in [(1280, 720), (1600, 900), (1920, 1080)]:
        for pass_idx, order in enumerate([ORDER_FWD, ORDER_REV, ORDER_FWD, ORDER_REV]):
            for ver in order:
                out = ROOT / f'eval1506-whole-{ver}-{w}.rgb32'
                args = [BENCH_EXE, CORE, DLLS[ver].replace('/mnt/c/', 'C:/'), str(w), str(h), '2', '50', '80', str(out).replace('/mnt/c/', 'C:/')] + (['sky'] if w == 1280 else [])
                t_start = datetime.datetime.now().isoformat()
                r = subprocess.run(args, capture_output=True, text=True, timeout=90)
                t_end = datetime.datetime.now().isoformat()
                assert r.returncode == 0, (ver, w, r.stdout, r.stderr)
                out.unlink(missing_ok=True)
                m = re.search(r'gpu_median_ms=([\d.]+)\s+gpu_mean_ms=([\d.]+)\s+gpu_min_ms=([\d.]+).*?nonfinite=(\d+)', r.stdout)
                assert m, r.stdout
                med_ms, mean_ms, min_ms = map(float, m.groups()[:3])
                nonfinite = int(m.group(4))
                if ver in ('v27', 'v29_fast'):
                    assert nonfinite == 0, (ver, w, r.stdout)
                whole_records.append({
                    'ver': ver, 'dll_sha256': DLL_SHAS[ver], 'width': w, 'pass': pass_idx,
                    'median_ms': med_ms, 'mean_ms': mean_ms, 'min_ms': min_ms,
                    'nonfinite': nonfinite, 'start': t_start, 'end': t_end,
                    'summary_line': [l for l in r.stdout.splitlines() if l.startswith('SUMMARY')][0]
                })
            print(f'  Width {w} pass {pass_idx}: ' + ', '.join(f'{v}={next(x["median_ms"] for x in reversed(whole_records) if x["ver"]==v and x["width"]==w):.4f}' for v in ORDER_FWD), flush=True)

    (TMP / 'eval1506_whole.json').write_text(json.dumps(whole_records, indent=2))

    print('=== 2. NVAPI PER-KERNEL 5-WAY SWEEPS (50/20) ===', flush=True)
    prof_records = []
    for w, h in [(1280, 720), (1600, 900), (1920, 1080)]:
        for pass_idx, order in enumerate([ORDER_FWD, ORDER_REV]):
            for ver in order:
                tag = f'{ver}-p{pass_idx}-{w}'
                trace = ROOT / f'eval1506-{tag}.csv'
                out = ROOT / f'eval1506-{tag}.rgb32'
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
                    fb_val = fb_map.get(x[4], -1)
                    assert fb_val != -1, f'Unknown kernel {x[4]}'
                    rows.append({'frame': frame, 'call': int(x[2]), 'name': x[4], 'FB': fb_val, 'gpu_ms': float(x[12]), 'start': int(x[13]), 'end': int(x[14])})
                frames = collections.defaultdict(list)
                for row in rows: frames[row['frame']].append(row)
                assert len(frames) == 20, f'Expected 20 measured frames, got {len(frames)}'
                assert all(len(rs) == 82 for rs in frames.values()), 'Expected exactly 82 launches per frame'
                by_fb = {}
                for fb_id in sorted(set(row['FB'] for row in rows)):
                    samples = [sum(row['gpu_ms'] for row in rs if row['FB'] == fb_id) for rs in frames.values()]
                    by_fb[str(fb_id)] = {'mean_ms': st.mean(samples), 'median_ms': st.median(samples)}
                by_name = {}
                for kname in sorted(set(row['name'] for row in rows)):
                    samples = [sum(row['gpu_ms'] for row in rs if row['name'] == kname) for rs in frames.values()]
                    by_name[kname] = {'FB': fb_map[kname], 'mean_ms': st.mean(samples), 'median_ms': st.median(samples)}
                sum_ms = st.mean(sum(row['gpu_ms'] for row in rs) for rs in frames.values())
                span_ms = st.mean((max(row['end'] for row in rs) - min(row['start'] for row in rs)) / 1e6 for rs in frames.values())
                prof_records.append({
                    'ver': ver, 'dll_sha256': DLL_SHAS[ver], 'pass': pass_idx, 'width': w,
                    'measured_frames': len(frames), 'launches_per_frame': 82, 'unknown_fb_count': 0,
                    'sum_ms': sum_ms, 'span_ms': span_ms, 'gap_ms': span_ms - sum_ms,
                    'by_FB': by_fb, 'by_name': by_name,
                    'summary_line': [l for l in r.stdout.splitlines() if l.startswith('SUMMARY')][0]
                })
            print(f'  NVAPI Width {w} pass {pass_idx}: ' + ', '.join(f'{v}={next(x["sum_ms"] for x in reversed(prof_records) if x["ver"]==v and x["width"]==w):.4f}' for v in ORDER_FWD), flush=True)

    (TMP / 'eval1506_nvapi.json').write_text(json.dumps(prof_records, indent=2))
    print('ALL EVAL 1506 RUNS DONE', flush=True)
finally:
    telem_proc.terminate()

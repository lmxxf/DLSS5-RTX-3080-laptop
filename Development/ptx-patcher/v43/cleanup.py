from pathlib import Path
import json,hashlib,os,signal,time,csv
p=Path(__file__).resolve().parent;v=json.loads((p/'validation.json').read_text());assert v['passed'];query=b'--query-gpu=timestamp,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu,clocks_event_reasons.sw_thermal_slowdown'
pidfile=p/'artifacts/telemetry-pid.json'
if pidfile.exists():
 pid=json.loads(pidfile.read_text())['pid'];proc=Path('/proc')/str(pid)
 if proc.exists():
  a=(proc/'cmdline').read_bytes().split(b'\0');assert a[0].endswith(b'nvidia-smi') and query in a;os.kill(pid,signal.SIGTERM)
time.sleep(.2);rows=[r for r in list(csv.reader((p/'artifacts/telemetry.csv').open()))[1:] if len(r)==7];(p/'telemetry-summary.json').write_text(json.dumps({'samples':len(rows),'temperature_min_c':min(float(r[1]) for r in rows),'temperature_max_c':max(float(r[1]) for r in rows),'sw_thermal_slowdown_active_samples':sum(r[6].strip()!='Not Active' for r in rows),'scope':'formal paired and repeat measurement interval, default DVFS'},indent=2)+'\n')
files=[f for f in (p/'artifacts').rglob('*') if f.is_file()];outdir=Path('/mnt/c/DLSS5-5090-dll/ptx-v43-bench');files += [f for f in outdir.rglob('*') if f.is_file()]
for c in json.loads((p/'candidates.json').read_text()).values():
 f=Path(c['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==c['sha256'];files.append(f)
manifest=[{'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files];(p/'cleanup.json').write_text(json.dumps({'status':'inventory sealed before deletion','removed_files':len(files),'logical_bytes':sum(r['bytes'] for r in manifest),'files':manifest},indent=2)+'\n')
for f in files:f.unlink()
import shutil
shutil.rmtree(p/'artifacts');shutil.rmtree(outdir)
for f in p.rglob('*.log'):f.unlink()
old=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in old};assert after==old;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n');result=json.loads((p/'cleanup.json').read_text());result.update(status='complete',per_run_log_fragments_remaining=0,protected_unchanged=True);(p/'cleanup.json').write_text(json.dumps(result,indent=2)+'\n');v.update(cleanup_complete=True,protected_unchanged_after_cleanup=True);(p/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print('cleanup',len(files),'files; log fragments 0')

from pathlib import Path
import json,hashlib,shutil,os,signal,csv,statistics as st,time
p=Path(__file__).resolve().parent;v=json.loads((p/'validation.json').read_text());assert v['data_checks_pass']
query='--query-gpu=timestamp,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu,clocks_event_reasons.sw_thermal_slowdown'
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:args=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if args and args[0].endswith(b'nvidia-smi') and query.encode() in args and b'-lms' in args and b'200' in args:os.kill(int(proc.name),signal.SIGTERM)
time.sleep(.2)
rows=list(csv.reader((p/'telemetry.csv').open()))[1:];valid=[r for r in rows if len(r)==7]
temp=[float(r[1]) for r in valid];active=[r for r in valid if float(r[5].split()[0])>=90];thermal=sum(r[6].strip()!='Not Active' for r in valid)
telemetry={'samples':len(valid),'temperature_min_c':min(temp),'temperature_max_c':max(temp),'temperature_mean_c':st.mean(temp),'sw_thermal_slowdown_active_samples':thermal,'active_ge90_samples':len(active),'active_sm_clock_median_mhz':st.median(float(r[2].split()[0]) for r in active),'active_power_median_w':st.median(float(r[4].split()[0]) for r in active),'scope':'entire V3.2 session, including builds, diagnostics and excluded screening; default DVFS; raw CSV retained'}
(p/'telemetry-summary.json').write_text(json.dumps(telemetry,indent=2)+'\n')
files=[]
for tree in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v32-bench')]:
 if tree.exists():files.extend(f for f in tree.rglob('*') if f.is_file())
for file in ['candidates.json','probes.json']:
 for r in json.loads((p/file).read_text()).values():
  f=Path(r['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];files.append(f)
assert len(files)==len(set(files))
manifest=[{'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
for f in files:f.unlink()
for tree in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v32-bench')]:
 if tree.exists():shutil.rmtree(tree)
result={'removed_files':len(manifest),'removed_bytes':sum(r['bytes'] for r in manifest),'files':manifest,'protected_paths_verified_before_cleanup':v['protected_paths'],'promoted_DLL_retained':(p/'selected.json').exists()}
(p/'cleanup.json').write_text(json.dumps(result,indent=2)+'\n');print(result['removed_files'],result['removed_bytes'],telemetry)

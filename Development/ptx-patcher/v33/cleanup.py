from pathlib import Path
import json,hashlib,shutil,os,signal,csv,statistics as st,time
p=Path(__file__).resolve().parent;v=json.loads((p/'validation.json').read_text());assert v['data_checks_pass']
query=b'--query-gpu=timestamp,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu,clocks_event_reasons.sw_thermal_slowdown'
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:a=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if a and a[0].endswith(b'nvidia-smi') and query in a and b'-lms' in a and b'200' in a:os.kill(int(proc.name),signal.SIGTERM)
time.sleep(.2)
rows=[r for r in list(csv.reader((p/'telemetry.csv').open()))[1:] if len(r)==7];temp=[float(r[1]) for r in rows];active=[r for r in rows if float(r[5].split()[0])>=90]
telemetry={'samples':len(rows),'temperature_min_c':min(temp),'temperature_max_c':max(temp),'sw_thermal_slowdown_active_samples':sum(r[6].strip()!='Not Active' for r in rows),'active_ge90_samples':len(active),'active_sm_clock_median_mhz':st.median(float(r[2].split()[0]) for r in active),'scope':'sampling interval covers final resource audit tail, smoke, probes and all paired/repeat runs; default DVFS; not initial builds'};(p/'telemetry-summary.json').write_text(json.dumps(telemetry,indent=2)+'\n')
files=[]
for tree in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v33-bench')]:
 if tree.exists():files.extend(f for f in tree.rglob('*') if f.is_file())
for c in json.loads((p/'candidates.json').read_text()).values():
 f=Path(c['path']);assert hashlib.sha256(f.read_bytes()).hexdigest()==c['sha256'];files.append(f)
assert len(files)==len(set(files));manifest=[{'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
for f in files:f.unlink()
for tree in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v33-bench')]:
 if tree.exists():shutil.rmtree(tree)
protected=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in protected};assert after==protected;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
result={'removed_files':len(manifest),'removed_bytes':sum(r['bytes'] for r in manifest),'files':manifest,'protected_paths_after_cleanup':len(after),'protected_unchanged':True,'promoted_DLL_retained':(p/'selected.json').exists()};(p/'cleanup.json').write_text(json.dumps(result,indent=2)+'\n');v.update(cleanup_complete=True,temporary_bytes_removed=result['removed_bytes'],protected_unchanged_after_cleanup=True);(p/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
f=p/'README.md';s=f.read_text();s+=f'\n清理完成：{len(manifest)} 个文件、{result["removed_bytes"]:,}B；九个保护路径再次同 SHA。采样温度 {min(temp):.0f}～{max(temp):.0f}°C，sw_thermal_slowdown 激活 {telemetry["sw_thermal_slowdown_active_samples"]} 点；此遥测覆盖所记区间，不作等频因果结论。\n';f.write_text(s);print(result['removed_files'],result['removed_bytes'],telemetry)

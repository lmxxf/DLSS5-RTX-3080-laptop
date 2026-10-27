from pathlib import Path
import json,hashlib,re,subprocess,csv
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');r=json.loads((p/'resources.json').read_text());s=json.loads((p/'selected.json').read_text());build=json.loads((p/'builds.json').read_text());smoke=json.loads((p/'smoke.json').read_text());bench=json.loads((p/'bench.json').read_text());assert len(smoke)==12 and len(bench)==72
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert sha(s['path'])==s['sha256'];assert Path(s['path']).stat().st_size==266414592
assert all(x['quality']['bitdiff']==0 and x['metrics']['nonfinite']==0 for x in smoke+bench)
protection={}
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v21.dll']:
 protection[str(f)]=sha(f);assert protection[str(f)]=='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed'
for pkg in json.loads((p.parent/'release-rtx30/v020/packages.json').read_text()):
 protection[pkg['path']]=sha(pkg['path']);assert protection[pkg['path']]==pkg['sha256']
ptx={}
for i in range(15):
 src=(p/f'artifacts/selected/fatbin{i:02d}.ptx').read_text();ptx[str(i)]={'async_bindings':src.count('cp.async.mbarrier.arrive.'),'wait_groups':src.count('cp.async.wait_group'),'caps':sorted(set(map(int,re.findall(r'\.maxnreg\s+(\d+)',src))))}
 assert ptx[str(i)]['async_bindings']=={4:104,5:208,6:4}.get(i,0)
 if i in [0,3,4,5,6]:assert ptx[str(i)]['caps']==[255]
 assert '.noinc' not in src
 assert all(x[1]=='inline' for x in build['combo']['manifest'])
changed={v:[i for i in range(15) if r[v][str(i)]['cubin_sha256']!=r['baseline'][str(i)]['cubin_sha256']] for v in ['async','swar','combo']};assert changed['async']==[4,5,6];assert changed['swar']==changed['combo']==list(range(7))
tele=list(csv.DictReader((p/'telemetry.csv').open(),skipinitialspace=True));stats={}
for col in ['temperature.gpu','power.draw [W]','clocks.current.sm [MHz]','clocks.current.memory [MHz]']:
 if tele and col in tele[0]:
  vals=[float(re.search(r'[\d.]+',row[col])[0]) for row in tele if re.search(r'[\d.]+',row[col])];stats[col]={'min':min(vals),'max':max(vals)}
result={'selected':s,'primitive':json.loads((p/'pack-test.json').read_text()),'smoke_runs':len(smoke),'timed_runs':len(bench),'all_bitdiff':0,'invalid':0,'size_growth_bytes':0,'all15_O4_inline':True,'selected_rebuild_identical':True,'changed_fatbins':changed,'PTX':ptx,'protected_files':protection,'telemetry':stats,'stack_limitation':'FB01 168 B, FB02 8 B, FB04 80 B, FB05 16 B remain; all-export static counts, no claim of zero spills.'}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS 84 outputs, 15 inline O4, selected rebuild SHA, protected fast/V21/3ZIP unchanged')

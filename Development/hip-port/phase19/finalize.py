from pathlib import Path
import sys,json,hashlib,shutil,subprocess,os,re,csv,datetime,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
base=r/'phase18/artifacts/selected/modules';candidate=p/'artifacts/m3/modules';mod=next(m for m in b.parse_ps1_modules(str(r/'hip/build-modules.ps1')) if m['name']=='c64-wave2-fast');b.PHASE19_WAVE_HALF=3;res=b.compile_one_module(mod,str(r/'hip'),str(candidate),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res
measured=json.loads((p/'candidate-b-m3-1920-run.json').read_text());assert res[4]==measured['module_hashes']['c64-wave2-fast.hsaco']
out=p/'artifacts/selected/modules';out.mkdir(parents=True,exist_ok=True)
for f in base.iterdir():
 if f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_'):continue
 shutil.copy2(candidate/f.name if f.stem=='c64-wave2-fast' else f,out/f.name)
(out/'AMPERE_WEIGHTS_W19').write_text('3\n');shutil.copy2(candidate/'c64-wave2-fast.generated.cu',out/'c64-wave2-fast.generated.cu')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();m={f.name:sha(f) for f in sorted(out.glob('*.hsaco'))};assert m==measured['module_hashes'];(p/'selected-modules.sha256.json').write_text(json.dumps(m,indent=2)+'\n');subprocess.run(['python3',str(r/'phase14/verify_modules.py'),'--modules',str(out)],check=True);(p/'cuda-load-verification.json').write_text((out.parent/'cuda-load-verification.json').read_text())
# Reject marker/module disagreement and pre-W19 Host, using symlinks only.
invalid=p/'artifacts/abi';invalid.mkdir(exist_ok=True)
for f in out.iterdir():
 if f.name=='AMPERE_WEIGHTS_W19':continue
 if f.suffix=='.hsaco' or f.name.startswith('AMPERE_'):(invalid/f.name).symlink_to(f)
(invalid/'AMPERE_WEIGHTS_W19').write_text('1\n');env=os.environ.copy();env.update(DLSS5_BENCH_WIDTH='1280',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_AMPERE_WEIGHTS='1',DLSS5_LAB_COMPACT_ALL='1',DLSS5_LAB_C256_SPLIT='0');abi=[]
for label,host,d in [('mismatch',p/'artifacts/benchmark_cuda_nn',invalid),('old-host',r/'phase18/artifacts/benchmark_cuda_nn',out)]:
 q=subprocess.run([str(host),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(d),'0','1'],env=env,capture_output=True,text=True,timeout=30);(p/(label+'.log')).write_text(q.stdout+q.stderr);assert q.returncode!=0,label;abi.append({'case':label,'returncode':q.returncode,'rejected':True})
(p/'abi.json').write_text(json.dumps(abi,indent=2)+'\n')
weights=[{'key':x[1],'c':int(x[2]),'old':int(x[3]),'new':int(x[4])} for x in re.finditer(r'W19_WEIGHT key=(\S+) c=(\d+) old=(\d+) new=(\d+)',(p/'candidate-b-m3-1920.log').read_text())];(p/'weights.json').write_text(json.dumps(weights,indent=2)+'\n')
samples=[]
for row in list(csv.reader((p/'abba-telemetry.csv').open()))[1:]:
 try:samples.append((datetime.datetime.strptime(row[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',v)[0]) for v in row[2:]]))
 except (ValueError,TypeError):pass
tele={}
for f in p.glob('*-run.json'):
 q=json.loads(f.read_text());a,z=map(datetime.datetime.fromisoformat,[q['begin'],q['end']]);ss=[s for s in samples if a<=s[0]<=z and s[-1]>=90];tele[f.stem]={'util90_samples':len(ss),**{k:float(np.median([s[i] for s in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry.json').write_text(json.dumps(tele,indent=2)+'\n')
protected={};root=Path('/mnt/c/DLSS5-5090-dll')
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v21.dll']:protected[str(f)]=sha(f);assert protected[str(f)]=='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed'
for q in json.loads((r.parent/'ptx-patcher/release-rtx30/v020/packages.json').read_text()):protected[q['path']]=sha(Path(q['path']));assert protected[q['path']]==q['sha256']
(p/'protected.json').write_text(json.dumps(protected,indent=2,ensure_ascii=False)+'\n');(p/'validation.json').write_text(json.dumps({'baseline':'Phase18 selected','candidates':2,'default_mask':3,'scope':'C64+C128 W16 FFN expand/contract/mix only;Frag8 Up/attention/diag unchanged','formal_ABBA_runs':24,'quick_runs':6,'all_bitdiff':0,'all_invalid':0,'active_LMem0':32,'C64_C128_regs_max':168,'C64_C128_OccW_min':12,'modules':40,'resolved_entries':1918,'source_rebuild_matches_measured':True,'ABI_rejections':abi,'external_v020_unchanged':True,'deployment':False,'push':False},indent=2)+'\n');print('PASS final source SHA/40/1918 ABI/resources and protected v020')

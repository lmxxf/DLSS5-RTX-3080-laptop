from pathlib import Path
import json,hashlib,re,subprocess
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');s=json.loads((p/'selected.json').read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();r={}
assert sha(s['path'])==s['sha256'];assert Path(s['path']).stat().st_size==266414592;assert all(x[1]=='inline' for x in s['manifest'])
primitive=json.loads((p/'decode-test.json').read_text());assert primitive['all_bitdiff']==0 and primitive['pairs']==33554432
rows=sum([json.loads((p/f).read_text()) for f in ['smoke.json','bench.json','confirm-1080.json']],[]);assert len(rows)==38;assert all(x['quality']['bitdiff']==0 and x['quality']['maxabs']==0 and x['metrics']['nonfinite']==0 for x in rows)
profiles={}
for f in ['profile.json','decode-profile.json']:
 x=json.loads((p/f).read_text());assert all(t['calls_per_frame']==82 and t['unique_kernels']==40 and t['event_vs_trace_bitdiff']==0 for t in x.values());profiles[f]={w:{k:t[k] for k in ['calls_per_frame','unique_kernels','event_vs_trace_bitdiff','sum_kernel_mean_ms','median_interkernel_gap_ms']} for w,t in x.items()}
ptx={}
for i in range(15):
 a=(p/f'artifacts/decode/fatbin{i:02d}.ptx').read_bytes();b=(p/f'artifacts/selected/fatbin{i:02d}.ptx').read_bytes();assert a==b;txt=a.decode();ptx[str(i)]={'sha256':hashlib.sha256(a).hexdigest(),'async_bindings':txt.count('cp.async.mbarrier.arrive.'),'prmt_even':txt.count('0xa280'),'prmt_odd':txt.count('0xb391'),'cap':sorted(set(map(int,re.findall(r'\.maxnreg\s+(\d+)',txt))))};assert ptx[str(i)]['prmt_even']==ptx[str(i)]['prmt_odd'];assert ptx[str(i)]['async_bindings']=={4:104,5:208,6:4}.get(i,0)
 if i in [0,3,4,5,6]:assert ptx[str(i)]['cap']==[255]
 assert 'diagnostic_ready_bypass' not in txt
protection={}
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v22.dll']:
 protection[str(f)]=sha(f);assert protection[str(f)]=='2705462fc74ca20208ebb83c08cd0e75613ddc220a7834b1e80f4c9aeb0eb90f'
for pkg in json.loads((p.parent/'release-rtx30/v020/packages.json').read_text()):
 protection[pkg['path']]=sha(pkg['path']);assert protection[pkg['path']]==pkg['sha256']
ns=json.loads((p/'nosleep-probe-bench.json').read_text());bad=json.loads((p/'sync-probe-bench.json').read_text());assert len(ns)==8 and all(x['bitdiff']==0 for x in ns);assert all(x['bitdiff']>0 for x in bad if x['tag']=='probe')
r={'selected':s,'primitive':primitive,'correct_smoke_timed_outputs':38,'profiles':profiles,'selected_rebuild_PTX_equal':True,'all15_O4_inline':True,'size_growth':0,'PTX':ptx,'protected_files':protection,'sync_bypass':'REJECTED: all probe outputs differ; cannot infer valid optimization savings','nosleep':'all bit identical, no net gain; not selected','regressions':10,'hardware_counter_limitation':'GPU timestamp intervals and static SASS are not dynamic stall or instruction counters; 70%-overlap roofline gap is not a measured recoverable loss.'}
(p/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS selected SHA, 38 strict outputs, four profiles, native async unchanged, release protection')

from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;r=p.parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();mods=p/'artifacts/selected/modules';actual={f.name:sha(f) for f in sorted(mods.glob('*.hsaco'))};assert actual==json.loads((p/'measured-modules.sha256.json').read_text())==json.loads((p/'selected-modules.sha256.json').read_text());assert len(actual)==40
loads=json.loads((mods.parent/'cuda-load-verification.json').read_text());assert len(loads)==40 and sum(x['entries'] for x in loads)==1918;(p/'cuda-load-verification.json').write_text(json.dumps(loads,indent=2)+'\n')
rows=json.loads((p/'results.json').read_text());formal={n:rr for n,rr in rows.items() if n.endswith('-nc-abba')};assert len(formal)==4 and sum(len(rr) for rr in formal.values())==12
for n,rr in formal.items():
 for w,x in rr.items():
  assert x['warmup']==50 and x['iterations']==80 and x['bitdiff']==x['invalid']==x['first_last']==0
  assert all(z['lmem']==0 for z in x['kernels'].values())
  m=json.loads((p/f'{n}-{w}-run.json').read_text());assert m['module_hashes']==(json.loads((r/'phase16/selected-modules.sha256.json').read_text()) if n.startswith('baseline') else actual)
  assert sha(p/'artifacts/benchmark_cuda_nn')==m['host_sha256']
assert json.loads((p/'primitive-results.json').read_text())['bitdiff']==0
single=json.loads((p/'single-kernel-results.json').read_text());assert len(single['results'])==6 and all(x['byte_diff']==0 for x in single['results'])
abi=json.loads((p/'abi-results.json').read_text());assert len(abi)==4 and all(x['rejected'] for x in abi)
root=Path('/mnt/c/DLSS5-5090-dll');external={}
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v21.dll']:
 external[str(f)]=sha(f);assert external[str(f)]=='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed'
for row in json.loads((r.parent/'ptx-patcher/release-rtx30/v020/packages.json').read_text()):
 f=Path(row['path']);external[str(f)]=sha(f);assert external[str(f)]==row['sha256']
(p/'protected-release-hashes.json').write_text(json.dumps(external,indent=2,ensure_ascii=False)+'\n')
(p/'validation.json').write_text(json.dumps({'baseline':'Phase16 selected (585fda1);Phase14 correct outputs unchanged','default':'V3 appended C32 FP16 enabled','modules':40,'resolved_entries':1918,'changed_modules':['c32-wave1-fast.hsaco'],'unchanged_modules':39,'source_rebuild_matches_measured':True,'formal_ABBA_runs':12,'warmup':50,'iterations':80,'all_formal_bitdiff':0,'all_formal_invalid':0,'all_formal_first_last':0,'active_kernels_LMem0':32,'nonUp_C32':'8KB /OccW11','Up_C32':'10KB /OccW9','isolated_C32_kernels_zero_byte_diff':6,'ABI_mismatch_rejections':4,'cache_counters':'not available;no cache-hit/residency claim','external_v020_hashes_unchanged':True,'deployment':False,'push':False},indent=2)+'\n');print('PASS final source/module/Host SHA,12 formal ABBA/6 isolated kernels/4 ABI controls;external v0.2.0 protected')

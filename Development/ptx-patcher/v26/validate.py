from pathlib import Path
import hashlib,json,re
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert s['V26_promoted'];assert sha(s['path'])==s['sha256'];assert Path(s['path']).stat().st_size==266414592;assert len(s['manifest'])==15 and all(x[1]=='inline' for x in s['manifest'])
primitive=json.loads((p/'primitives.json').read_text());assert primitive['coordinate_slots']==768 and primitive['decode_permutation_bitdiff']==0 and primitive['mapped_masks_tested']==64 and primitive['exact_matrix_mismatches']==0
alias=json.loads((p/'alias-tests.json').read_text());assert len(alias)==5 and all(x['word_bitdiff_against_independent_upfront_lowhigh']==0 for x in alias)
rows=json.loads((p/'smoke.json').read_text())+json.loads((p/'bench.json').read_text());assert len(rows)==39 and all(x['metrics']['nonfinite']==0 for x in rows)
for x in rows:
 q=x['quality']
 if q['repeat']:assert q['repeat']['bitdiff']==0
 if x['width']==1280:assert q['sky_sign_changes']==0
 if x['variant']=='lowhigh':
  assert set(q['vs'])=={'baseline','v1'} and all(t['psnr_db']>=58 for t in q['vs'].values())
summary=json.loads((p/'summary.json').read_text());assert all(all(d['gain_percent']>0 for d in r['directions'].values()) for r in summary.values())
ptx={}
for fb in range(15):
 a=(p/f'artifacts/decode/fatbin{fb:02}.ptx').read_bytes();b=(p/f'artifacts/selected/fatbin{fb:02}.ptx').read_bytes();assert a==b;txt=a.decode();ptx[str(fb)]={'sha256':hashlib.sha256(a).hexdigest(),'cap':sorted(set(map(int,re.findall(r'\.maxnreg\s+(\d+)',txt)))),'mapped_selector_5410':txt.count('0x5410'),'mapped_selector_7632':txt.count('0x7632'),'async_bindings':txt.count('cp.async.mbarrier.arrive.')}
 assert ptx[str(fb)]['async_bindings']=={4:104,5:208,6:4}.get(fb,0)
 if fb in [0,3,4,5,6]:assert ptx[str(fb)]['cap']==[255]
audit=json.loads((p/'codegen-audit.json').read_text());assert all(r['totals']['backup_moves']==0 for r in audit.values())
pro=json.loads((p/'protected-before-cleanup.json').read_text())
for f,r in pro.items():assert sha(f)==r['sha256']
r={'selected':s,'primitive':primitive,'alias_tests':alias,'total_bench_runs':39,'timed_V24_candidate_runs':24,'V1_reference_50_80_runs':6,'smoke_runs':9,'all_repeat_bitdiff':0,'cross_version_bit_exact':False,'all_final_output_nonfinite':0,'all_sky_sign_changes':0,'same_round_quality':summary,'all15_O4_original_slots':True,'rebuild_same_PTX_and_DLL':True,'PTX':ptx,'codegen_backup_moves_all_FBs':0,'protected_files':pro,'regressions':10,'scope':'FP16 summation order changed. PSNR compares three deterministic bench outputs to V2.4/V1; not an absolute native-SM120 or whole-network FP32 gold claim.'}
(p/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS: lowhigh mapping and alias guards, 39 finite deterministic runs, quality gates, paired gains, reproducible recommended DLL')

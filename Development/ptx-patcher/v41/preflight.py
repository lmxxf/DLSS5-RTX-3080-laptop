from pathlib import Path
import json,hashlib,re,subprocess,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());sp=json.loads((p/'specs.json').read_text());r=json.loads((p/'resources.json').read_text());sm=json.loads((p/'smoke.json').read_text());assert len(sm)==len(cs)*3;assert cs['baseline']['sha256']=='749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca'
for row in sm:
 assert row['quality']['quality_pass'] and row['quality']['nonfinite']==0
 if not cs[row['variant']]['approximate']:assert row['quality']['bitdiff']==row['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(r[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'up-primitive.json').read_text())['passed'];base=sp['baseline'];up_modes=['up_occ_keep','up_add_fb6','up_add_fb4pool'];pool='cc_split_swin_16h_proj_pool_512_chained_fp8';dec='cc_dec_input_upsample_1024_512_tilesync_fp8'
for n in up_modes:
 for k,q in r[n].items():
  for f in ['STACK','STL','LDL']:assert q[f]<=r['baseline'][k][f],(n,k,f)
  assert q['resident_CTA_per_SM']>=r['baseline'][k]['resident_CTA_per_SM'],(n,k)
full=json.loads((p/'artifacts/build-records-full.json').read_text());folds={};coverage={}
for mode,mods in full.items():
 ups=[x for m in mods for x in m['up_pairs'] if x['applied']];coverage[mode]={'compiled_UP_applied':len(ups),'compiled_cross_UP_applied':sum(x.get('original_cross_block',False) for x in ups),'compiled_splits_deleted':len({(x['FB'],x['kernel'],x['split_index']) for x in ups if x.get('split_deleted')})}
 for x in ups:
  if x.get('original_cross_block'):assert x['CFG_proof']['all_paths_unclobbered']
for mode in ['zero_fb23456']:
 fbs={m['FB']:sum(x['kind']=='pack3' and x['range']==[0.,0.] for x in m['ranges']) for m in full[mode]};assert fbs=={2:40,3:40};folds[mode]={'incremental_sites':80,'total_sites':580,'increment_per_FB':fbs}
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';cache={}
def funcs(f):
 st=f.stat();key=(st.st_dev,st.st_ino)
 if key not in cache:cache[key]={q.splitlines()[0].strip():q for q in re.split('Function : ',subprocess.check_output([tool,'-sass',str(f)],text=True))[1:]}
 return cache[key]
isolation={}
for mode,s in sp.items():
 if mode=='baseline':continue
 for fb in set(range(15))-set(s['fbs']):
  for ext in ['ptx','cubin','bin']:assert (p/f'artifacts/{mode}/fatbin{fb:02}.{ext}').read_bytes()==(p/f'artifacts/baseline/fatbin{fb:02}.{ext}').read_bytes()
 extra=set(s['up_entries'])-set(base['up_entries']);newpack=set(s.get('pack4_entries',[]));zerofbs=set(s['zero_fbs'])-set(base['zero_fbs']);names=[n for n,q in r['baseline'].items() if n not in extra|newpack and q['FB'] not in zerofbs]
 for n in names:
  fb=r['baseline'][n]['FB'];assert funcs(p/f'artifacts/{mode}/fatbin{fb:02}.cubin')[n]==funcs(p/f'artifacts/baseline/fatbin{fb:02}.cubin')[n],(mode,n)
 isolation[mode]={'unchanged_FBs':sorted(set(range(15))-set(s['fbs'])),'unchanged_active_entries_SASS':names,'new_UP_entries':sorted(extra),'new_Pack4_entries':sorted(newpack),'new_zero_FBs':sorted(zerofbs)}
(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');(p/'zero-fold-audit.json').write_text(json.dumps(folds,indent=2)+'\n');(p/'up-coverage.json').write_text(json.dumps({'scope':'compiled module counts; unchanged modules inherited V4.0 recipe','by_mode':coverage,'all_path_proof_reference':'../v40/cross-block-up-audit.json','proof_reference_SHA256':hashlib.sha256((p.parent/'v40/cross-block-up-audit.json').read_bytes()).hexdigest()},indent=2)+'\n')
qualified=[n for n in cs if n!='baseline' and not sp[n].get('components') and cs[n]['sha256']!=cs['baseline']['sha256']];identical=[n for n in cs if n!='baseline' and not sp[n].get('components') and n not in qualified];assert set(up_modes)<=set(qualified);(p/'timing-candidates.json').write_text(json.dumps(qualified,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(sm),'single_factor_timing_candidates':qualified,'baseline_identical_not_timed':identical,'prebuilt_joint_candidates':[n for n,s in sp.items() if s.get('components')],'UP_only_STACK_STL_LDL_nonincrease':True,'UP_only_official_CTA_SM_nondecrease':True,'strict_increment_quality':['up_occ_keep','up_add_fb6','up_add_fb4pool','zero_fb23456'],'V4.0_reference_SHA256':cs['baseline']['sha256']},indent=2)+'\n');print('PASS',len(qualified),'singles and three prebuilt joints;',identical,'identical')

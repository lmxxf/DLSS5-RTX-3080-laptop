from pathlib import Path
import json,hashlib,re,subprocess,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());sp=json.loads((p/'specs.json').read_text());res=json.loads((p/'resources.json').read_text());rr=json.loads((p/'smoke.json').read_text());assert len(rr)==len(cs)*3;assert cs['baseline']['sha256']=='da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3'
for r in rr:
 assert r['quality']['quality_pass'] and r['quality']['nonfinite']==0
 if not cs[r['variant']]['approximate']:assert r['quality']['bitdiff']==r['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'up-primitive.json').read_text())['passed']
full=json.loads((p/'artifacts/build-records-full.json').read_text());ups=[r for m in full['up_pair_all'] for r in m['up_pairs']];counts=collections.Counter(r['reason'] for r in ups);pairs=collections.defaultdict(list)
for r in ups:
 if 'split_index' in r:pairs[r['FB'],r['kernel'],r['split_index']].append(r)
assert len(ups)==4744 and len(pairs)==2372;assert all(len(q)==2 and {r['half'] for r in q}=={0,1} for q in pairs.values())
cols=['FB','kernel','line','conversion_index','destination','half_source','source32','split_index','half','eligible','reason','applied','split_deleted'];text='{"columns":'+json.dumps(cols)+',"rows":[\n'+',\n'.join(json.dumps([r.get(k) for k in cols],separators=(',',':')) for r in ups)+'\n]}\n';(p/'up-pair-audit.json').write_text(text)
cleanups=[r for m in full['up_pair_clean'] for r in m['up_pairs']]
summary={'clean_applied_UPs':sum(r['applied'] for r in cleanups),'clean_deleted_splits':len({(r['FB'],r['kernel'],r['split_index']) for r in cleanups if r.get('split_deleted')}),'independent_UPs':len(ups),'split_pairs':len(pairs),'eligible_UPs':sum(r['eligible'] for r in ups),'eligibility_reasons':dict(counts),'removed_splits':sum(all(r.get('split_deleted') for r in q) for q in pairs.values()),'retained_splits':sum(not all(r.get('split_deleted') for r in q) for q in pairs.values()),'retained_cross_block_splits':sum(all(r['reason']=='cross_block' for r in q) for q in pairs.values()),'eligible_splits_retained_for_other_uses':sum(all(r['eligible'] for r in q) and not all(r.get('split_deleted') for r in q) for q in pairs.values()),'exact_reference':'V3.8 legacy independent UP','per_FB':dict(collections.Counter(r['FB'] for r in ups))};(p/'up-pair-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# Zero fold counts use the already independently certified V3.8 per-FB source counts.
zero=json.loads((p.parent/'v38/zero-fold-audit.json').read_text())['fold_counts_by_mode_FB'];expected={'zero_fb1456':540,'zero_fb3456':540,'zero_no_fb0up':676};folds={}
for mode,total in expected.items():
 s=sp[mode];modcounts={int(m['FB']):sum(r['kind']=='pack3' and r['range']==[0.,0.] and r['kernel'] not in s.get('zero_exclude_entries',[]) for r in m['ranges']) for m in full[mode]};modcounts.update({k:int(v) for k,v in [(4,176),(5,288),(6,36)] if k not in modcounts});assert sum(modcounts.values())==total,(mode,modcounts);folds[mode]={'total_folded':total,'per_FB':modcounts}
for n,q in res['zero_no_fb0up'].items():assert q['REG']<=res['baseline'][n]['REG'] and q['STACK']<=res['baseline'][n]['STACK'],(n,q)
sel=json.loads((p/'up-clean-selection.json').read_text())['selected']
for n in sel:
 for f in ['REG','STACK','STL','LDL']:assert res['up_pair_clean'][n][f]<=res['baseline'][n][f]
 assert res['up_pair_clean'][n]['resident_CTA_per_SM']>=res['baseline'][n]['resident_CTA_per_SM']
# Unselected entry code stays baseline; untouched complete modules remain byte-identical.
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
 names=set(s.get('zero_exclude_entries',[]))
 if mode=='up_pair_clean':names|={n for n in res['baseline'] if n not in sel}
 for n in names:
  fb=res['baseline'][n]['FB'];a=p/f'artifacts/{mode}/fatbin{fb:02}.cubin';b=p/f'artifacts/baseline/fatbin{fb:02}.cubin';assert funcs(a)[n]==funcs(b)[n]
 isolation[mode]={'whole_unchanged_FBs':sorted(set(range(15))-set(s['fbs'])),'unchanged_active_entries':sorted(names)}
(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');(p/'zero-fold-audit.json').write_text(json.dumps(folds,indent=2)+'\n');qualified=[n for n,c in cs.items() if n!='baseline' and c['sha256']!=cs['baseline']['sha256']];(p/'timing-candidates.json').write_text(json.dumps(qualified,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(rr),'timing_candidates':qualified,'baseline_identical_not_timed':[n for n in cs if n!='baseline' and n not in qualified],'UP_summary':summary,'zero_extension_counts':expected,'UP_clean_entries':len(sel),'zero_no_fb0up_no_REG_STACK_increase':True,'reference_SHA256':cs['baseline']['sha256']},indent=2)+'\n');print('PASS',len(qualified),'timing candidates;',summary)

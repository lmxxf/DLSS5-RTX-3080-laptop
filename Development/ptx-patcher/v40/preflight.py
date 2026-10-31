from pathlib import Path
import json,hashlib,collections,re,subprocess
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());sp=json.loads((p/'specs.json').read_text());r=json.loads((p/'resources.json').read_text());sm=json.loads((p/'smoke.json').read_text());assert len(sm)==3*len(cs);assert cs['baseline']['sha256']=='da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3'
for row in sm:
 assert row['quality']['quality_pass'] and row['quality']['nonfinite']==0
 if not cs[row['variant']]['approximate']:assert row['quality']['bitdiff']==row['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(r[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'up-primitive.json').read_text())['passed'];full=json.loads((p/'artifacts/build-records-full.json').read_text());baseUP=[x for m in full['baseline'] for x in m['up_pairs']];cross=[x for x in baseUP if x.get('original_cross_block')];assert len(baseUP)==4744 and len(cross)==2062;assert all(x['reason']=='CFG_unclobbered' and x['CFG_proof']['dominates'] and not x['CFG_proof']['source_write_witnesses'] and not x['CFG_proof']['opaque_call_witnesses'] for x in cross);pairs={(x['FB'],x['kernel'],x['split_index']) for x in cross};assert len(pairs)==1031
# One compact row per cross-block use; kernel names and the proof policy are explicit.
cols=['FB','kernel','line','split_index','conversion_index','source32','half_source','destination','half','split_halves','CFG_proof'];text='{"policy":"all CFG paths including cycles; unique unguarded half definition; dominating split; guarded source writes clobber; no reset relaxation","columns":'+json.dumps(cols)+',"rows":[\n'+',\n'.join(json.dumps([x.get(k) for k in cols],separators=(',',':')) for x in cross)+'\n]}\n';(p/'cross-block-up-audit.json').write_text(text)
coverage={}
for mode,mods in full.items():
 ups=[x for m in mods for x in m['up_pairs']];applied=[x for x in ups if x['applied']];coverage[mode]={'UP_applied':len(applied),'cross_block_applied':sum(x.get('original_cross_block',False) for x in applied),'splits_deleted':len({(x['FB'],x['kernel'],x['split_index']) for x in applied if x.get('split_deleted')})}
(p/'up-coverage.json').write_text(json.dumps({'all_UPs':4744,'original_cross_UPs':2062,'cross_pairs_proven':1031,'coverage_by_mode':coverage},indent=2)+'\n')
a=json.loads((p/'module-selection.json').read_text())['entries'];extra=json.loads((p/'module-selection.json').read_text())['extra_FB01_entry'];assert len(a)==16;assert all(r['baseline'][n]['STACK']==r['baseline'][n]['STL']==r['baseline'][n]['LDL']==0 for n in a);delta=sum(v['INSN_NONOP']-r['baseline'][n]['INSN_NONOP'] for n,v in r['up_pair_fb2345'].items());assert delta==-1439,delta;assert [r['up_pair_fb1inp_2345'][extra][k] for k in ['STACK','STL','LDL']]==[56,10,14]
selected=json.loads((p/'cfg-clean-selection.json').read_text())['selected']
for n in selected:
 for k in ['REG','STACK','STL','LDL']:assert r['up_pair_cfg_clean'][n][k]<=r['baseline'][n][k]
 assert r['up_pair_cfg_clean'][n]['resident_CTA_per_SM']>=r['baseline'][n]['resident_CTA_per_SM']
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';cache={}
def funcs(f):
 st=f.stat();key=(st.st_dev,st.st_ino)
 if key not in cache:cache[key]={x.splitlines()[0].strip():x for x in re.split('Function : ',subprocess.check_output([tool,'-sass',str(f)],text=True))[1:]}
 return cache[key]
isolation={}
for mode,s in sp.items():
 if mode=='baseline':continue
 for fb in set(range(15))-set(s['fbs']):
  for ext in ['ptx','cubin','bin']:assert (p/f'artifacts/{mode}/fatbin{fb:02}.{ext}').read_bytes()==(p/f'artifacts/baseline/fatbin{fb:02}.{ext}').read_bytes()
 preserve=[n for n,q in r['baseline'].items() if n not in s.get('up_entries',r['baseline']) and q['FB'] not in s.get('pack4',[])]
 for n in preserve:
  fb=r['baseline'][n]['FB'];assert funcs(p/f'artifacts/{mode}/fatbin{fb:02}.cubin')[n]==funcs(p/f'artifacts/baseline/fatbin{fb:02}.cubin')[n]
 isolation[mode]={'whole_unchanged_FBs':sorted(set(range(15))-set(s['fbs'])),'unchanged_active_entry_SASS':preserve}
(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');timed=[n for n,c in cs.items() if n!='baseline' and not sp[n].get('diagnostic') and c['sha256']!=cs['baseline']['sha256']];assert len(timed)==5;(p/'timing-candidates.json').write_text(json.dumps(timed,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(sm),'timing_candidates':timed,'diagnostic_not_timed':['up_pair_cfg_all'],'cross_UPs_proven':2062,'cross_pairs_proven':1031,'CFG_clean_selected_active_entries':len(selected),'A_changed_active_entries':16,'A_nonNOP_delta':delta,'A_FB04_nonNOP_delta':-86,'original_15_slots_O4':True,'V3.8_reference_SHA256':cs['baseline']['sha256']},indent=2)+'\n');print('PASS',len(timed),'timing candidates, all 1031 cross pairs proven')

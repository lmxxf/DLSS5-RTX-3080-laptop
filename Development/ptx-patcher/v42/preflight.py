from pathlib import Path
import json,hashlib,collections,re,subprocess
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());sp=json.loads((p/'specs.json').read_text());r=json.loads((p/'resources.json').read_text());sm=json.loads((p/'smoke.json').read_text());assert len(sm)==len(cs)*3;assert cs['baseline']['sha256']=='749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca'
for x in sm:
 assert x['quality']['quality_pass'] and x['quality']['nonfinite']==0
 if not cs[x['variant']]['approximate']:assert x['quality']['bitdiff']==x['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(r[n])==38 and all(x[1]=='inline' for x in c['manifest'])
prim=json.loads((p/'quad-primitive.json').read_text());assert prim['passed'] and prim['total_quad_cases']==33554432 and prim['machine_evidence']['pack4_quad']['core_count']==7
for mode,fbs in [('pack4_fb0_nopre',[0]),('pack4_fb1_clean',[1]),('pack4_quad_clean',[2,3])]:
 for n,q in r[mode].items():
  if q['FB'] in fbs:
   for f in ['STACK','STL','LDL']:assert q[f]<=r['baseline'][n][f],(mode,n,f)
full=json.loads((p/'artifacts/build-records-full.json').read_text());audits=[x for m in full['pack4_quad_fb23'] for x in m['quads']];cols=['FB','kernel','pack_line','down_lines','sources','halves','destination','block','proofs'];rows=[dict(FB=a['FB'],kernel=a['kernel'],**q) for a in audits for q in a['accepted']];(p/'quad-fusion-audit.json').write_text('{"columns":'+json.dumps(cols)+',"rows":[\n'+',\n'.join(json.dumps([q[k] for k in cols],separators=(',',':')) for q in rows)+'\n]}\n');summary={'all_export_fused_pairs':len(rows),'launched_entry_fused_pairs':sum(a['fused'] for a in audits if a['kernel'] in r['baseline']),'per_kernel':{a['kernel']:{'FB':a['FB'],'fused':a['fused'],'rejections':a['rejections']} for a in audits},'actual_active_PRMT_delta':sum(q['PRMT']-r['baseline'][n]['PRMT'] for n,q in r['pack4_quad_fb23'].items()),'actual_active_nonNOP_delta':sum(q['INSN_NONOP']-r['baseline'][n]['INSN_NONOP'] for n,q in r['pack4_quad_fb23'].items())};(p/'quad-fusion-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
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
 names=[n for n,q in r['baseline'].items() if n not in s.get('pack4_entries',[])+s.get('quad_entries',[]) and q['FB'] not in s.get('quad_fbs',[])]
 for n in names:
  fb=r['baseline'][n]['FB'];assert funcs(p/f'artifacts/{mode}/fatbin{fb:02}.cubin')[n]==funcs(p/f'artifacts/baseline/fatbin{fb:02}.cubin')[n],(mode,n)
 isolation[mode]={'unchanged_FBs':sorted(set(range(15))-set(s['fbs'])),'unchanged_active_entry_SASS':names}
(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');timed=[n for n,c in cs.items() if n!='baseline' and not sp[n].get('diagnostic') and not sp[n].get('components') and c['sha256']!=cs['baseline']['sha256']];assert 'pack4_fb0_nopre' in timed and 'pack4_quad_fb23' in timed;(p/'timing-candidates.json').write_text(json.dumps(timed,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(sm),'timing_candidates':timed,'baseline_identical_not_timed':[n for n in sp if n!='baseline' and not sp[n].get('diagnostic') and not sp[n].get('components') and n not in timed],'quad_core_SASS':7,'quad_cases':33554432,'quad_active_fused_pairs':summary['launched_entry_fused_pairs'],'quad_active_PRMT_delta':summary['actual_active_PRMT_delta'],'resource_policy':'STACK/STL/LDL nonincrease for A/B/quad-clean; no mechanical REG exclusion','baseline_SHA256':cs['baseline']['sha256']},indent=2)+'\n');print('PASS',timed,'quad active pairs/PRMT delta',summary['launched_entry_fused_pairs'],summary['actual_active_PRMT_delta'])

from pathlib import Path
import json,hashlib,subprocess,re,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());sp=json.loads((p/'specs.json').read_text());r=json.loads((p/'resources.json').read_text());sm=json.loads((p/'smoke.json').read_text());assert len(sm)==3*len(cs);assert cs['baseline']['sha256']=='749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca'
for x in sm:assert x['quality']['quality_pass'] and x['quality']['nonfinite']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(r[n])==38 and all(x[1]=='inline' for x in c['manifest'])
prim=json.loads((p/'quad-primitive.json').read_text());assert prim['passed'] and prim['total_quad_cases']==33554432 and prim['machine_evidence']['pack4_quad']['core_count']==7
sel=json.loads((p/'clean-selection.json').read_text());
for n in sel['FB01_selected']:
 for k in ['STACK','STL','LDL']:assert r['fb123_pack4_quad_clean'][n][k]<=r['baseline'][n][k]
 assert r['fb123_pack4_quad_clean'][n]['resident_CTA_per_SM']>=r['baseline'][n]['resident_CTA_per_SM']
full=json.loads((p/'artifacts/build-records-full.json').read_text());quads={}
for mode,mods in full.items():
 a=[x for m in mods for x in m['quads']];quads[mode]={'all_export_fused':sum(x['fused'] for x in a),'active_fused':sum(x['fused'] for x in a if x['kernel'] in r['baseline']),'FB01_active_fused':sum(x['fused'] for x in a if x['FB']==1 and x['kernel'] in r['baseline'])}
(p/'quad-coverage.json').write_text(json.dumps(quads,indent=2)+'\n');assert sum(q['INSN_NONOP'] for q in r['fb1_pack4_fb23_quad'].values())==144131
# Unchanged entire modules (including FB00) and inactive entry code are checked.
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';cache={}
def funcs(f):
 st=f.stat();key=(st.st_dev,st.st_ino)
 if key not in cache:cache[key]={q.splitlines()[0].strip():q for q in re.split('Function : ',subprocess.check_output([tool,'-sass',str(f)],text=True))[1:]}
 return cache[key]
iso={}
for mode,s in sp.items():
 if mode=='baseline':continue
 for fb in set(range(15))-set(s['fbs']):
  for ext in ['ptx','cubin','bin']:assert (p/f'artifacts/{mode}/fatbin{fb:02}.{ext}').read_bytes()==(p/f'artifacts/baseline/fatbin{fb:02}.{ext}').read_bytes()
 names=[n for n in r['baseline'] if n not in s.get('pack4_entries',[])+s.get('quad_entries',[])]
 for n in names:
  fb=r['baseline'][n]['FB'];assert funcs(p/f'artifacts/{mode}/fatbin{fb:02}.cubin')[n]==funcs(p/f'artifacts/baseline/fatbin{fb:02}.cubin')[n],(mode,n)
 iso[mode]={'unchanged_FBs':sorted(set(range(15))-set(s['fbs'])),'unchanged_active_entry_SASS':names}
(p/'isolation-validation.json').write_text(json.dumps(iso,indent=2)+'\n');timed=[n for n in cs if n!='baseline' and not sp[n].get('diagnostic') and cs[n]['sha256']!=cs['baseline']['sha256']];assert len(timed)==3;(p/'timing-candidates.json').write_text(json.dumps(timed,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(sm),'timing_candidates':timed,'diagnostic_not_timed':['fb123_quad_diagnostic'],'all_candidates_FB00_byte_identical':True,'candidate_1_active_nonNOP':144131,'FB01_quad_selected':sel['FB01_selected'],'quad_diagnostic_FB01_active_fusions':quads['fb123_quad_diagnostic']['FB01_active_fused'],'quad_core_SASS':7,'quad_GPU_cases':33554432,'reference_SHA256':cs['baseline']['sha256']},indent=2)+'\n');print('PASS 3 timing candidates; FB01 quad selected',sel['FB01_selected'])

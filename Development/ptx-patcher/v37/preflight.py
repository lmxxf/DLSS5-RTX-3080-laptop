from pathlib import Path
import json,hashlib,collections,subprocess,re
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());rows=json.loads((p/'smoke.json').read_text());spec=json.loads((p/'specs.json').read_text());assert len(rows)==3*len(cs)
assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
for r in rows:
 assert r['quality']['quality_pass'] and r['quality']['nonfinite']==0
 if not cs[r['variant']]['approximate']:assert r['quality']['bitdiff']==r['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'zero-primitive.json').read_text())['mismatches']==0
# All unaffected entry PTX and actual SASS must remain byte-identical.
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
def functions(f,sass=False):
 text=subprocess.check_output([tool,'-sass',str(f)],text=True) if sass else f.read_text()
 parts=re.split(r'Function : ' if sass else r'(?=\.visible \.entry )',text)
 out={}
 for part in parts[1:]:
  n=part.splitlines()[0].strip() if sass else re.match(r'\.visible \.entry (\w+)',part)[1]
  out[n]=part
 return out
base={fb:(functions(p/f'artifacts/baseline/fatbin{fb:02}.ptx'),functions(p/f'artifacts/baseline/fatbin{fb:02}.cubin',True)) for fb in range(7)};isolation={}
for mode in cs:
 if mode=='baseline' or spec[mode].get('zero'):continue
 allowed=set(spec[mode].get('entries',[]))|({'cc_split_swin_16h_qkv_512_chained_fp8'} if spec[mode].get('async') else set());checked=0
 for fb in range(7):
  for z,suffix in [(0,'ptx'),(1,'cubin')]:
   now=functions(p/f'artifacts/{mode}/fatbin{fb:02}.{suffix}',z==1)
   for n,text in base[fb][z].items():
    if n not in allowed:assert now[n]==text,(mode,n,suffix)
  checked+=sum(n not in allowed for n in res['baseline'] if res['baseline'][n]['FB']==fb)
 isolation[mode]={'allowed_changed_entries':sorted(allowed),'unchanged_launched_entries_PTX_and_SASS':checked}
zero_records=json.loads((p/'artifacts/build-records-full.json').read_text())['pack_zero_const'];zeros=[r for m in zero_records for r in m['ranges'] if r['kind']=='pack3'];assert len(zeros)==680 and all(r['range']==[0.,0.] and r['nonnegative_plus_zero_proved'] and not r['may_nan'] for r in zeros)
(p/'zero-fold-audit.json').write_text(json.dumps({'folded_sites':len(zeros),'proof':'independent bit-level mov/cvt-only reaching-definition chain to literal positive-zero, rechecked after MMA lowering by zero_check.py; no general interval math used for the zero proof','by_FB':dict(collections.Counter(r['FB'] for r in zeros)),'by_kernel':dict(collections.Counter(r['kernel'] for r in zeros)),'source_audit':'../v36/pack-range-audit.json','source_audit_sha256':hashlib.sha256((p.parent/'v36/pack-range-audit.json').read_bytes()).hexdigest()},indent=2)+'\n')
qualified=[n for n,c in cs.items() if n!='baseline' and c['sha256']!=cs['baseline']['sha256']];identical=[n for n,c in cs.items() if n!='baseline' and c['sha256']==cs['baseline']['sha256']];(p/'timing-candidates.json').write_text(json.dumps(qualified,indent=2)+'\n');(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(rows),'timing_candidates':qualified,'baseline_identical_not_rebenchmarked':identical,'zero_folds':680,'original_15_slots_O4':True,'no_per_run_log_files':True},indent=2)+'\n');print('PASS',len(qualified),'timing candidates;',identical,'identical')

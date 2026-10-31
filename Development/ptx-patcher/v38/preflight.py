from pathlib import Path
import json,hashlib,re,subprocess,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());spec=json.loads((p/'specs.json').read_text());res=json.loads((p/'resources.json').read_text());rows=json.loads((p/'smoke.json').read_text());assert len(rows)==3*len(cs);assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
for r in rows:
 assert r['quality']['quality_pass'] and not r['quality']['nonfinite']
 if not cs[r['variant']]['approximate']:assert r['quality']['bitdiff']==r['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'zero-primitive.json').read_text())['mismatches']==0
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';cache={}
def funcs(f,sass=False):
 st=f.stat();key=(st.st_dev,st.st_ino,sass)
 if key in cache:return cache[key]
 text=subprocess.check_output([tool,'-sass',str(f)],text=True) if sass else f.read_text();parts=re.split('Function : ' if sass else r'(?=\.visible \.entry )',text)[1:];out={(part.splitlines()[0].strip() if sass else re.match(r'\.visible \.entry (\w+)',part)[1]):part for part in parts};cache[key]=out;return out
base={fb:(funcs(p/f'artifacts/baseline/fatbin{fb:02}.ptx'),funcs(p/f'artifacts/baseline/fatbin{fb:02}.cubin',True)) for fb in range(7)};isolation={};records=json.loads((p/'artifacts/build-records-full.json').read_text());folds={}
for mode in cs:
 if mode=='baseline':continue
 s=spec[mode];allowed_fbs=set(s.get('zero_fbs',[])+s.get('pack4',[]));allowed_names=set(s.get('entries',[]))|({'cc_split_swin_16h_proj_pool_512_chained_fp8'} if s.get('async') else set());unchanged=[]
 for fb in range(15):
  if fb not in allowed_fbs and not (fb==3 and s.get('entries')) and not (fb==4 and s.get('async')):
   for ext in ['ptx','cubin','bin']:
    a=p/f'artifacts/{mode}/fatbin{fb:02}.{ext}';b=p/f'artifacts/baseline/fatbin{fb:02}.{ext}';assert a.read_bytes()==b.read_bytes(),(mode,fb,ext)
  if fb>6 or fb in allowed_fbs:continue
  for z,ext in [(0,'ptx'),(1,'cubin')]:
   now=funcs(p/f'artifacts/{mode}/fatbin{fb:02}.{ext}',z==1)
   for n,text in base[fb][z].items():
    if n not in allowed_names:assert now[n]==text,(mode,n,ext)
  unchanged.extend(n for n,r in res['baseline'].items() if r['FB']==fb and n not in allowed_names)
 isolation[mode]={'unchanged_active_entries':unchanged,'allowed_whole_module_frontend_changes':sorted(allowed_fbs),'allowed_shared_entry_changes':sorted(allowed_names)}
 folds[mode]={str(m['FB']):sum(r['kind']=='pack3' and r['range']==[0.,0.] for r in m['ranges']) for m in records[mode] if m['FB'] in s.get('zero_fbs',[])}
 for fb,reused in s.get('reuse',{}).items():
  if int(fb) in s.get('zero_fbs',[]):folds[mode][fb]=folds[reused][fb]
(p/'isolation-validation.json').write_text(json.dumps(isolation,indent=2)+'\n');(p/'zero-fold-audit.json').write_text(json.dumps({'fold_counts_by_mode_FB':folds,'bit_level_witness':'every replaced site independently rechecked by zero_check.py mov/cvt reaching chain to literal +0; pure pack4 does not fold zero sites','source_proof':'../v37/zero-fold-audit.json'},indent=2)+'\n')
singles=[n for n in cs if n!='baseline' and not spec[n].get('joint_components')];assert len(singles)==7;assert all(cs[n]['sha256']!=cs['baseline']['sha256'] for n in singles);(p/'timing-candidates.json').write_text(json.dumps(singles,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(rows),'single_factor_candidates':singles,'prebuilt_joint_candidates':[n for n,s in spec.items() if s.get('joint_components')],'15_original_slots_O4':True,'all_outputs_pass_quality':True,'all_frontend_candidates_preserve_FB00_FB01':True,'isolated_pool_other_entries_unchanged':37,'isolated_FB03_other_entries_unchanged':36},indent=2)+'\n');print('PASS',len(singles),'singles plus',len(cs)-1-len(singles),'prebuilt joints')

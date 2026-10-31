"""Normalized audit storage: one canonical range table, no duplicated site dumps."""
from pathlib import Path
import json,hashlib,collections
p=Path(__file__).resolve().parent

def save_ranges(records):
 kernels=sorted({r['kernel'] for r in records});kid={n:i for i,n in enumerate(kernels)};defs=[];ids={};rows=[]
 for r in records:
  dd=[]
  for d in r['definitions']:
   key=(kid[r['kernel']],d['index'],d['text'])
   if key not in ids:ids[key]=len(defs);defs.append(list(key))
   dd.append(ids[key])
  rows.append([r['FB'],kid[r['kernel']],r['line'],r['source'],r['destination'],r['kind'],r['range'],r['may_nan'],r['nonnegative_plus_zero_proved'],dd])
 header={'scope':'8944 surviving conversions; normalized lossless table, kernel and definition references interned','counts':{k:sum(r['kind']==k for r in records) for k in ['pack3','pack4','generic']},'columns':['FB','kernel_id','line','source','destination','kind','interval','may_nan','nonnegative_plus_zero_proved','definition_ids'],'kernels':kernels,'definition_columns':['kernel_id','instruction_index','text'],'definitions':defs}
 # One row per site/definition remains diffable, without 20 repeated key lines.
 prefix=json.dumps({k:v for k,v in header.items() if k not in ['definitions']},indent=2)[:-2]
 text=prefix+',\n  "definitions": [\n'+',\n'.join('    '+json.dumps(r,separators=(',',':')) for r in defs)+'\n  ],\n  "rows": [\n'+',\n'.join('    '+json.dumps(r,separators=(',',':')) for r in rows)+'\n  ]\n}\n';json.loads(text);(p/'pack-range-audit.json').write_text(text)

def save_build_summary(data):
 out={}
 for mode,mods in data.items():
  out[mode]=[]
  for m in mods:
   kernels={}
   for r in m['runs']:
    q=kernels.setdefault(r['kernel'],{'runs':0,'max_temporary_b32_pool':0,'shared_native_events':0});q['runs']+=1;q['max_temporary_b32_pool']=max(q['max_temporary_b32_pool'],r['temporary_b32_peak']);q['shared_native_events']+=r['shared_native_events']
   out[mode].append({k:m[k] for k in ['FB','begin','end','message']}|{'kernel_audit':kernels,'range_counts':dict(collections.Counter(r['kind'] for r in m['ranges'])),'full_generated_record_sha256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()})
 (p/'build-records.json').write_text(json.dumps(out,indent=2)+'\n')

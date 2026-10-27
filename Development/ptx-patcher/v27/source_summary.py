from pathlib import Path
import json,collections,hashlib
p=Path(__file__).resolve().parent;r=json.loads((p/'source-audit.json').read_text());out={'scope':r['scope'],'FB_peaks':r['FB_peaks'],'fatbins':{}};symbols={}
def compact(x):
 if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
 if isinstance(x,list):return [compact(v) for v in x]
 if isinstance(x,str) and x.startswith('symbol:'):
  key='symbol#'+hashlib.sha256(x.encode()).hexdigest()[:16];symbols[key]=x;return key
 return x
for fb,ks in r['fatbins'].items():
 root=collections.Counter();leaf=collections.Counter();reasons=collections.Counter();peak=collections.Counter();writers=collections.Counter();mapped=alias=0;parser_delta=[]
 for name,k in ks.items():
  root.update(k['root_categories']);leaf.update(k['value_leaf_combinations']);reasons.update(k['eligibility_reasons']);mapped+=k['mapped_static_run_events'];alias+=k['same_basic_block_pure_alias_duplicate_events']
  for rec in k['records']:
   if rec['run_pool_b32']==r['FB_peaks'][fb]['active_peak'] and rec['live_at_first_peak']:peak['+'.join(rec['leaf_categories'])]+=1
  for w in k['shared_writer_may_origins']:writers['+'.join(w['value_categories'])]+=1
  d=k['mapped_eligibility_parser_delta']
  if d['added_with_complete_opcode_parser'] or d['removed_with_complete_opcode_parser']:parser_delta.append(name)
 out['fatbins'][fb]={'mapped_run_events':mapped,'nonmapped_run_events':sum(root.values()),'root_categories':dict(root),'value_leaf_combinations':dict(leaf),'eligibility_reasons':dict(reasons),'first_peak_live_sources_in_FB_maximum_runs':dict(peak),'shared_writer_leaf_kinds_by_static_store_site':dict(writers),'safe_same_BB_alias_duplicates':alias,'eligibility_parser_delta_kernels':parser_delta}
compacted=compact(r);compacted['symbol_dictionary']=symbols;(p/'source-audit.json').write_text(json.dumps(compacted,indent=2)+'\n');(p/'source-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

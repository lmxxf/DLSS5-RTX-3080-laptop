from pathlib import Path
import json,collections
p=Path(__file__).resolve().parent;r=json.loads((p/'source-summary.json').read_text());detail=json.loads((p/'source-audit.json').read_text());lines=['# Nonmapped operand provenance','','Unit: one unique decoded register per static MMA run in the active kernels. CFG may-reaching definitions describe all possible origins; this is not a dynamic frame frequency, and memory loads do not by themselves prove weight semantics. Symbol names are interned in source-audit.json.','','| FB | Mapped run events | Nonmapped run events | Leaf combinations |','|---:|---:|---:|---|']
for fb,x in r['fatbins'].items():lines.append(f'| {fb} | {x["mapped_run_events"]} | {x["nonmapped_run_events"]} | '+ '; '.join(f'{k}: {v}' for k,v in x['value_leaf_combinations'].items())+' |')
lines+=['','## Why the largest decoded pools remain','','At the first peak of every active run achieving the FB maximum, the compositions below agree. Counts are simultaneously live decoded pairs, each occupying two b32 temporaries, not total physical kernel registers.','','| FB | Global pairs at peak | Shared pairs at peak | Temporary b32 peak | Global pointer root |','|---:|---:|---:|---:|---|']
for fb in ['1','2','3','4','5']:
 groups=collections.defaultdict(collections.Counter);roots=set()
 for name,k in detail['fatbins'][fb].items():
  for x in k['records']:
   if x['run_pool_b32']==detail['FB_peaks'][fb]['active_peak'] and x['live_at_first_peak']:
    groups[(name,x['run'])]['+'.join(x['leaf_categories'])]+=1
    for mem in x['memory_sources']:
     if '.global' in mem['op']:roots.update(mem['roots'])
 compositions={tuple(sorted(x.items())) for x in groups.values()};assert len(compositions)==1;d=dict(next(iter(compositions)));lines.append(f'| {fb} | {d.get("global_load",0)} | {d.get("shared_load",0)} | {detail["FB_peaks"][fb]["active_peak"]} | '+', '.join(sorted(roots))+' |')
lines+=['','Global bases are traced to actual argument offsets; they are not all relabeled weights without a host-structure proof. Shared producers are also audited: FB01 shared_storage is written from local FP8 quantization; FB02/03 and FB04/05 may include local quantization plus global/async-copy sources. This motivates layout/storage experiments, but does not establish safe same-lane FP16 forwarding across a shared-memory exchange.','', 'Current multidef mode disables the same-basic-block restriction. Rejected pack/phi paths and numerical quantization semantics require proof before widening forwarding. No same-basic-block pure-mov duplicate decode identities were found.','', 'The audit parser recognizes :: qualifiers. The production definition parser was hardened likewise; all 112 entry mappings remained identical, and a full V2.6 rebuild remained byte-identical. See parser-scope-check.json and parser-binary-check.json.']
(p/'source-results.md').write_text('\n'.join(lines)+'\n')

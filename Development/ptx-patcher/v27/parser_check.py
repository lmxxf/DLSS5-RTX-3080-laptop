from pathlib import Path
import sys,re,json
from functools import partial
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b,ptx_mapped as pm
complete=pm.INS;old=re.compile(complete.pattern.replace('(?:::[\\w.]+)*',''),complete.flags);out={};entries=0
for fb in range(7):
 raw=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text()
 for e in re.split(r'(?=\.visible \.entry )',raw)[1:]:
  name=re.match(r'\.visible \.entry (\w+)',e)[1];pm.INS=old;a=b.stock_pack_sources(e,local_only=False);pm.INS=complete;z=b.stock_pack_sources(e,local_only=False);pm.INS=old;entries+=1
  if dict(a)!=dict(z):out[f'{fb}:{name}']={'added':sorted(set(z)-set(a)),'removed':sorted(set(a)-set(z)),'value_changes':[r for r in a.keys()&z.keys() if a[r]!=z[r]]}
(p/'parser-scope-check.json').write_text(json.dumps({'entries':entries,'mapping_deltas':out,'legacy_parser_qualifier_blindspot':old.pattern!=complete.pattern,'legacy_pattern':old.pattern,'fixed_pattern':complete.pattern},indent=2)+'\n');print(entries,'entry mappings checked; deltas',out)

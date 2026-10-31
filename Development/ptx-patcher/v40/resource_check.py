from pathlib import Path
import json
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());out={}
for mode,rs in r.items():
 out[mode]={'totals':{k:sum(x[k] for x in rs.values()) for k in ['INSN_NONOP','HMMA','PRMT','STL','LDL']},'resource_changes':{n:{k:[r['baseline'][n][k],v[k]] for k in ['REG','STACK','STL','LDL','INSN_NONOP','resident_CTA_per_SM'] if r['baseline'][n][k]!=v[k]} for n,v in rs.items() if v!=r['baseline'][n]}}
assert out['baseline']['totals']=={'INSN_NONOP':150672,'HMMA':13188,'PRMT':19525,'STL':100,'LDL':101};assert all(v['totals']['HMMA']==13188 for v in out.values());(p/'resource-validation.json').write_text(json.dumps(out,indent=2)+'\n');print({n:v['totals']['INSN_NONOP']-150672 for n,v in out.items()})

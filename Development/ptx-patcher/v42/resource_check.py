from pathlib import Path
import json
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());out={}
for mode,rs in r.items():out[mode]={'totals':{k:sum(q[k] for q in rs.values()) for k in ['INSN_NONOP','HMMA','PRMT','STL','LDL']},'changes':{n:{k:[r['baseline'][n][k],q[k]] for k in ['REG','STACK','STL','LDL','INSN_NONOP','PRMT','resident_CTA_per_SM'] if q[k]!=r['baseline'][n][k]} for n,q in rs.items() if q!=r['baseline'][n]}}
assert out['baseline']['totals']=={'INSN_NONOP':145461,'HMMA':13188,'PRMT':18781,'STL':99,'LDL':100};assert all(v['totals']['HMMA']==13188 for v in out.values());(p/'resource-validation.json').write_text(json.dumps(out,indent=2)+'\n');print({n:v['totals']['INSN_NONOP']-145461 for n,v in out.items()})

from pathlib import Path
import json
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());out={}
for mode,rs in r.items():
 out[mode]={'totals':{k:sum(x[k] for x in rs.values()) for k in ['INSN_NONOP','HMMA','PRMT','STL','LDL']},'changed_entries':{n:{k:[r['baseline'][n][k],x[k]] for k in ['REG','STACK','STL','LDL','INSN_NONOP','resident_CTA_per_SM'] if x[k]!=r['baseline'][n][k]} for n,x in rs.items() if x!=r['baseline'][n]}}
assert out['baseline']['totals']=={'INSN_NONOP':150672,'HMMA':13188,'PRMT':19525,'STL':100,'LDL':101}
(p/'resource-validation.json').write_text(json.dumps({'baseline_SHA256':'da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3','same_HMMA_all':all(out[n]['totals']['HMMA']==13188 for n in out),'modes':out,'scope':'38 actually launched entries, static counts and actual API occupancy; not per-frame issued counts'},indent=2)+'\n');print({n:v['totals']['INSN_NONOP']-150672 for n,v in out.items()})

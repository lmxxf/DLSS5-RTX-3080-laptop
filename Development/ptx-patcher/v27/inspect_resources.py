from pathlib import Path
import json,re,subprocess
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';baseline=json.loads((p.parent/'v26/resources.json').read_text())['decode'];active={r['name'] for w in json.loads((p.parent/'v25/launch-params.json').read_text()).values() for r in w['calls']};rows={'baseline':baseline}
for name,fbs in [('a',range(7)),('b',range(7)),('ab',range(7)),('cap0-168',[0]),('a_cap0',[0]),('prefix168',[0])]:
 rows[name]={}
 for fb in fbs:
  f=p/f'artifacts/{name}/fatbin{fb:02}.cubin';s=subprocess.check_output([tool,'-res-usage',str(f)],text=True);kernels={}
  for m in re.finditer(r'Function\s+(\S+):\s*(.*)',s):kernels[m[1]]={k:int(v) for k,v in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}
  rows[name][str(fb)]={'kernels':kernels,'all_export_max_STACK':max(x['STACK'] for x in kernels.values()),'active_max_STACK':max([x['STACK'] for n,x in kernels.items() if n in active] or [0])}
  print(name,fb,rows[name][str(fb)]['all_export_max_STACK'],rows[name][str(fb)]['active_max_STACK'],flush=True)
(p/'resources.json').write_text(json.dumps(rows,indent=2)+'\n')

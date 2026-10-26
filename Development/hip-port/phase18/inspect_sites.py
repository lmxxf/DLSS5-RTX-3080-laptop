from pathlib import Path
import json,subprocess,re
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';rows={}
for site,row in json.loads((p/'site-builds.json').read_text()).items():
 f=Path(row['modules'])/(row['module']+'.hsaco');s=subprocess.run([tool,'-res-usage',str(f)],capture_output=True,text=True,check=True).stdout;(p/(site+'-resources.txt')).write_text(s);kernels={}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',s):kernels[m[1]]={a:int(b) for a,b in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}
 rows[site]={'module':row['module'],'kernels':kernels};print(site,'maxStack',max(k['STACK'] for k in kernels.values()),flush=True)
(p/'site-resources.json').write_text(json.dumps(rows,indent=2)+'\n')

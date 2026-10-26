from pathlib import Path
import json,subprocess
from check_run import check_variant
p=Path(__file__).resolve().parent;builds=json.loads((p/'site-builds.json').read_text());rows={}
for site in ['contract','result','v','av','byteout','c32-prefix','c32-v']:
 tag=('quick2-'+site) if site=='byteout' else ('quick-'+site)
 if site in ['byteout','c32-prefix','c32-v']:
  subprocess.run(['python3',str(p/'bench.py'),tag,'--modules',builds[site]['modules'],'--warmup','3','--iterations','5'],check=True)
 d=check_variant(tag,False);assert len(d)==3,(site,d);numeric=all(x['bitdiff']==x['invalid']==x['first_last']==0 for x in d.values());local=all(x['LMem0'] for x in d.values());rows[site]={'numeric':numeric,'LMem0':local,'runs':d,'modules':builds[site]['modules'],'eligible_ABBA':numeric and local};(p/'site-quick-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('SITE',site,'numeric',numeric,'LMem0',local,flush=True)

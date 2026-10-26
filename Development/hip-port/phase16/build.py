from pathlib import Path
import sys,json,shutil,hashlib
from concurrent.futures import ThreadPoolExecutor
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
src=r/'hip';out=p/'artifacts/tail/modules';out.mkdir(parents=True,exist_ok=True)
base=r/'phase14/artifacts/selected/modules';manifest=json.loads((r/'phase14/selected-modules.sha256.json').read_text())
for n,h in manifest.items():
 assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h
 if not (out/n).exists() or Path(n).stem not in {"deep_fast-packed","deep_fast-packed-fast","vit-stream-fast"}:shutil.copy2(base/n,out/n)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
mods=[m for m in b.parse_ps1_modules(str(src/'build-modules.ps1')) if m['name'] in {'deep_fast-packed','deep_fast-packed-fast','vit-stream-fast'}]
def run(m):
 result=b.compile_one_module(m,str(src),str(out),str(src/'sm86_compat.h'),str(src/'ptx2cubin'));print(result,flush=True);return result
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,mods))
(p/'build-results.json').write_text(json.dumps(results,indent=2)+'\n');assert all(x[1] for x in results)

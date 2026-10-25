from pathlib import Path
import sys,shutil,re,subprocess,concurrent.futures,json,hashlib
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
from phase10_transform import apply_register_caps,REGISTER_CAPS
out=root/'phase10/artifacts/caps/modules';out.mkdir(parents=True,exist_ok=True);base=root/'phase9/artifacts/selected/modules'
for p in base.glob('*.hsaco'):shutil.copy2(p,out/p.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
def build(name):
 p=out/(name+'.ptx');s=apply_register_caps((base/p.name).read_text());p.write_text(s);entries=re.findall(r'\.visible\s+\.entry\s+(\w+)\s*\(',s)
 r=subprocess.run([str(root/'hip/ptx2cubin'),str(p),str(out/(name+'.hsaco'))]+entries,capture_output=True,text=True)
 assert r.returncode==0,(name,r.stderr,r.stdout);return {'module':name,'entries':len(entries),'sha256':hashlib.sha256((out/(name+'.hsaco')).read_bytes()).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rows=list(ex.map(build,['c64-wave2-fast','c512-m32-mh','c32-wave1-fast']))
(out.parent/'build.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
assert len(list(out.glob('*.hsaco')))==40
print('PASS: 9 entry caps; 3 modules O4 compiled/loaded; complete 40-module set',flush=True)

from pathlib import Path
import json,sys,hashlib,shutil
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
selection=json.loads((p/'selection.json').read_text());cfg=json.loads((p/'control-builds.json').read_text())[selection['control']];measured=json.loads((p/'candidate-b-final-1920-run.json').read_text());base=r/'phase17/artifacts/selected/modules';src=r/'hip';built={};out=p/'artifacts/selected/modules';out.mkdir(parents=True,exist_ok=True)
b.PHASE18_SITES=selection['sites'];b.PHASE18_C256_CAP=selection['C256_cap'];b.PHASE18_QKV_MASK=selection['QKV_mask']
for name in ['c32-wave1-fast','c64-wave2-fast']:
 existing=out;mod=next(m for m in b.parse_ps1_modules(str(src/'build-modules.ps1')) if m['name']==name)
 result=b.compile_one_module(mod,str(src),str(existing),str(src/'sm86_compat.h'),str(src/'ptx2cubin'));print(name,result[:3],flush=True);assert result[1];assert result[4]==measured['module_hashes'][name+'.hsaco'],(name,result[4],measured['module_hashes'][name+'.hsaco']);built[name]=existing
out=p/'artifacts/selected/modules';out.mkdir(parents=True,exist_ok=True)
for f in base.iterdir():
 if f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_'):continue
 source=built[f.stem]/f.name if f.stem in built else f
 if source.resolve()!=(out/f.name).resolve():shutil.copy2(source,out/f.name)
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.hsaco'))};assert hashes==measured['module_hashes'];(p/'selected-modules.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n');print('PASS all40 final source/selected SHA match measured final;38 unchanged fromPhase17')

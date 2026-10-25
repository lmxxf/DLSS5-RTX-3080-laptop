from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;r=p.parent;art=p/'artifacts';art.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
manifest=json.loads((r/'phase14/selected-modules.sha256.json').read_text());base=r/'phase14/artifacts/selected/modules';assert all(sha(base/n)==h for n,h in manifest.items())
(p/'phase14-baseline-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
expected=json.loads((r/'phase14/f32-fixed-modules.sha256.json').read_text());out=art/'reference/modules';out.mkdir(parents=True,exist_ok=True)
for n,h in expected.items():
 src=r/('phase14/artifacts/f32-fixed/modules' if n=='deep_fast-packed-fast.hsaco' else 'phase1/artifacts/f32-modules')/n;assert sha(src)==h,(src,h);shutil.copy2(src,out/n)
(p/'reference-modules.sha256.json').write_text(json.dumps(expected,indent=2)+'\n')
for kind in ['fixed','f32-fixed']:
 out=art/kind/'modules';out.mkdir(parents=True,exist_ok=True);src=(base if kind=='fixed' else art/'reference/modules')/'deep_fast-packed-fast.hsaco';shutil.copy2(src,out/src.name)
for name in ['cuda_probe.py','reference.py','layout_probe.hip','trace_layout.py','build_probe.py','coverage.py','actual_qkv.py','rounding_probe.hip','rounding_audit.py']:
 src=r/'phase14'/name;s=src.read_text().replace("p=r/'phase14'","p=r/'phase15'").replace("p=Path(__file__).resolve().parent","p=Path(__file__).resolve().parent").replace("'../phase14/","'../phase15/")
 # Keep imports of the production phase14_transform: that ABI fix is the baseline.

 if not (p/name).exists():(p/name).write_text(s)
for sub in ['actual-qkv','gold-capture']:
 out=art/sub;out.mkdir(exist_ok=True)
 for f in (r/'phase14/artifacts'/sub).glob('*.bin'):shutil.copy2(f,out/f.name)
gold=r/'phase14/artifacts/gold/f32-720p-1280x768.rgb32';g=json.loads((r/'phase14/gold-manifest.json').read_text());assert sha(gold)==g['sha256'];(p/'gold-baseline.json').write_text(json.dumps(g,indent=2)+'\n')
source={'native_modules':str(base),'native_manifest_sha256':sha(r/'phase14/selected-modules.sha256.json'),'F32_manifest_sha256':sha(r/'phase14/f32-fixed-modules.sha256.json'),'gold_sha256':sha(gold),'copied_regression_sources':{n:sha(r/'phase14'/n) for n in ['trace_layout.py','layout_probe.hip','coverage.py','rounding_audit.py','rounding_probe.hip','reference.py']},'network_QKV_origin':'actual CUDA execution on synthetic benchmark image; NOT game capture'}
(p/'regression-provenance.json').write_text(json.dumps(source,indent=2)+'\n');print('Prepared pinned Phase14 native/F32/gold and long-term primitive fixtures')

from diag15b_paths import ROOT
"""Recreate only frozen diagnostic inputs; never rewrite Phase15 fixtures/golds."""
from pathlib import Path
import numpy as np,ast,json,hashlib,shutil
p=Path(__file__).resolve().parent;r=p.parent;root=ROOT;root.mkdir(exist_ok=True);(root/'inputs').mkdir(exist_ok=True)
s=(p/'make_inputs.py').read_text();tree=ast.parse(s);functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['resize','encode']];ns={'np':np};exec(compile(ast.Module(body=functions,type_ignores=[]),'frozen-fixture-functions','exec'),ns)
pins=json.loads((p/'pinned-image-outputs.json').read_text())['cases'];manifest=json.loads((p/'input-manifest.json').read_text());runs=json.loads((p/'regression-runs.json').read_text());rows=[]
y,x=np.mgrid[:720,:1296];pix=(y*1296+x).astype(np.uint32);bits=np.stack([((pix*37+c*7919)%0x3c01).astype(np.uint16) for c in range(3)],2);ramp=bits.view(np.float16).astype(np.float32)
for name,w,h,vh,kind in [('ramp1024',1024,1024,1024,'ramp'),('canonical720',1280,768,720,'canonical'),('ramp720',1280,768,720,'ramp'),('canonical1024',1024,1024,1024,'canonical')]:
 a=np.ones((h,w,4),np.float32)
 if kind=='ramp':
  v=ns['encode'](ns['resize'](ramp,w,vh),1);yy=np.where(np.arange(h)<vh,np.arange(h),2*vh-2-np.arange(h));a[:,:,:3]=v[yy]
 else:
  yy,xx=np.mgrid[:h,:w]
  for c,(vx,vy,offset) in enumerate([(17,31,0),(23,13,100),(7,41,200)]):a[:,:,c]=((xx*vx+yy*vy+offset)%1024).astype(np.float32)/np.float32(1024)
 f=root/'inputs'/(name+'.rgba32');a.tofile(f);sha=hashlib.sha256(f.read_bytes()).hexdigest();row={'case':name,'processing':[w,h],'visible':[w,vh],'input_file':str(f),'input_sha256':sha,'kind':kind}
 if name=='ramp1024':key='1024-square/codec-ramp-wp1';assert sha==pins[key]['input_sha256'];row.update(frozen_output_native=pins[key]['native_sha256'],frozen_output_f32=pins[key]['reference_sha256'])
 if name=='ramp720':key='720/codec-ramp-wp1';assert sha==pins[key]['input_sha256'];row.update(frozen_output_native=pins[key]['native_sha256'],frozen_output_f32=pins[key]['reference_sha256'])
 if name=='canonical720':
  run=next(x for x in runs if x['label']=='baseline-1280' and x['mode']=='400');assert sha==run['input_SHA256'][0];row['frozen_output_native']=run['output_sha256'][0];run=next(x for x in runs if x['label']=='baseline-1280' and x['mode']=='f32');row['frozen_output_f32']=run['output_sha256'][0]
 rows.append(row)
# Recompose the immutable Phase14 F32 reference inside this diagnostic directory.
mods=root/'reference';mods.mkdir(exist_ok=True);expected=json.loads((p/'reference-modules.sha256.json').read_text())
for n,sha in expected.items():
 f=r/('phase14/artifacts/f32-fixed/modules' if n=='deep_fast-packed-fast.hsaco' else 'phase1/artifacts/f32-modules')/n;assert hashlib.sha256(f.read_bytes()).hexdigest()==sha;shutil.copy2(f,mods/n)
(p/'diag15b-inputs.json').write_text(json.dumps(rows,indent=2)+'\n');print([(x['case'],x['input_sha256']) for x in rows])

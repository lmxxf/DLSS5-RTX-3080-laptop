from common import *
import shutil,re,base64
D=read(P/'deployment.json');rows=[]
def metrics(text):
 line=next(x for x in text.splitlines() if x.startswith('SUMMARY '));return {k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',line)}
for pf in D['profiles']:
 label=pf['label'];stage=Path(pf['stage']);args=[ROOT/'nvngx.dll_runner/bench_sky.exe',DRIVER,win(stage/'nvngx_dlssnr.dll'),'1280','720','2','3','5',win(TOOLS/(label+'-native.rgb32')),'sky'];runrow=run(args,tag=label+' native Feature18');m=metrics(runrow['stdout']);assert m['nonfinite']==0 and 'SNIP_CREATE18=0x00000001' in runrow['stdout'];rows.append({'label':label,'test':'Windows native NGX Feature18 load/create/evaluate','returncode':0,'nonfinite':0,'NR_sha256':sha(stage/'nvngx_dlssnr.dll'),'metrics':m,'process_output':runrow['stdout'],'stderr':runrow['stderr']});write(P/'smoke-results.json',rows)
 if label=='Magpie':continue
 before={f.relative_to(stage).as_posix() for f in stage.rglob('*') if f.is_file()};ini=(stage/'OptiScaler.ini').read_bytes()
 try:
  for n in ['ffx_loader_smoke.exe','ffx_nr_smoke.exe']:shutil.copy2(TOOLS/n,stage/n)
  shutil.copy2(ROOT/'nvngx_dlss.dll',stage/'nvngx_dlss.dll')
  loader=run([stage/'ffx_loader_smoke.exe',win(stage/'amd_fidelityfx_dx12.dll')],cwd=stage,tag=label+' FFX loader')
  ffx=run([stage/'ffx_nr_smoke.exe',DRIVER,win(stage/'amd_fidelityfx_dx12.dll'),'1280','720','2','3','5',win(TOOLS/(label+'-ffx.rgb32')),'sky'],cwd=stage,tag=label+' FFX-NGX-NR composition');m=metrics(ffx['stdout']);assert m['nonfinite']==0
  host=(stage/'OptiScaler.log').read_bytes();text=host.decode('utf-8-sig',errors='replace');assert 'composition:' in text and 'detail 1.00, colour 1.00' in text and 'running before SR' in text;assert "game's FFX input" in text and 'primary feature ready' in text
  rows.append({'label':label,'test':'Windows FFX loader and FFX→NGX→NR before-SR composition','returncode':0,'loader_returncode':loader['returncode'],'nonfinite':0,'NR_sha256':sha(stage/'nvngx_dlssnr.dll'),'NR_composition_observed':True,'default_strength':'1.0/1.0','metrics':m,'process_output':ffx['stdout'],'stderr':ffx['stderr'],'loader_output':loader['stdout'],'host_output':text,'host_raw_sha256':hashlib.sha256(host).hexdigest(),'host_raw_base64':base64.b64encode(host).decode()});write(P/'smoke-results.json',rows)
 finally:
  (stage/'OptiScaler.ini').write_bytes(ini)
  for f in list(stage.rglob('*')):
   if f.is_file() and f.relative_to(stage).as_posix() not in before:f.unlink()
assert len(rows)==5 and all(x['returncode']==x['nonfinite']==0 for x in rows);print('PASS five Windows tests:3 native Feature18 +2 FFX→NGX→NR;stage helper/logs removed')

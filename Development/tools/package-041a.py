#!/usr/bin/env python3
"""Rebuild the regular 0.41-a ZIP from verified 0.41 plus a frozen, validated payload.
CPU only. Does not install, upload, or alter the original archive.
"""
import argparse, hashlib, json, pathlib, shutil, tempfile, zipfile

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()

def require(ok,msg):
 if not ok:raise ValueError(msg)

def relname(name):
 n=name.replace('\\','/');p=pathlib.PurePosixPath(n)
 require(not p.is_absolute() and '..' not in p.parts and ':' not in n,'unsafe archive path: '+name)
 return n

def check_stage(stage):
 lines=(stage/'SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines();seen=set()
 for line in lines:
  require(len(line)>66 and line[64:66]=='  ','invalid SHA line');n=relname(line[66:]);require(n not in seen,'duplicate SHA path');seen.add(n)
  require(digest(stage/n)==line[:64].lower(),'staged SHA mismatch '+n)
 files={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
 require(files==seen|{'SHA256SUMS.txt'},'manifest file set mismatch')
 return seen

def build(baseline,payload_file,output):
 payload=json.loads(payload_file.read_text())
 require(payload.get('version')=='0.41-a' and payload.get('kind')=='optiscaler','regular 0.41-a payload only')
 require(payload.get('source_commit') and payload.get('validated') is True,'frozen source and explicit completed validation required')
 require(digest(baseline)==payload['baseline_sha256'],'baseline archive SHA mismatch')
 require(not output.exists(),'output already exists; never overwrite release artifacts')
 checks=payload['validation_receipts'];require(checks,'validation receipts required')
 for item in checks:require(digest(pathlib.Path(item['source']))==item['sha256'],'validation receipt fingerprint mismatch')
 overlays=payload['files'];require(any(relname(f['target'])=='dlss5-amd.addon64' for f in overlays),'fresh regular addon required')
 require(not any(relname(f['target']) in ('LmxxfNrRuntime.dll','dxgi.dll','OptiScaler.ini') for f in overlays),'do not replace RE9/host payload or personal host settings')
 with tempfile.TemporaryDirectory(prefix='package-041a-',dir=output.parent) as temp:
  stage=pathlib.Path(temp)/'stage';stage.mkdir()
  with zipfile.ZipFile(baseline) as z:
   seen=set()
   for e in z.infolist():
    n=relname(e.filename);require(n not in seen,'duplicate baseline ZIP entry');seen.add(n)
    if e.is_dir():continue
    target=stage/n;target.parent.mkdir(parents=True,exist_ok=True)
    with z.open(e) as source,target.open('wb') as dest:shutil.copyfileobj(source,dest)
  check_stage(stage)
  overlay_targets=set()
  for f in overlays:
   n=relname(f['target']);require(n not in overlay_targets,'duplicate overlay target');overlay_targets.add(n)
   source=pathlib.Path(f['source']);require(digest(source)==f['sha256'],'payload SHA mismatch '+n)
   dest=stage/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
  assets=stage/'DLSS5-AMD/native-game-tiled-assets';module_root=assets/'HIP';total=0
  expected=payload['modules_per_arch']
  for arch in ('gfx1200','gfx1201'):
   modules=sorted((module_root/arch).glob('*.hsaco'));require(len(modules)==expected,'module count '+arch);total+=len(modules)
   (module_root/arch/'SHA256SUMS').write_text(''.join(digest(f)+'  '+f.name+'\n' for f in modules))
  modules=sorted(module_root.rglob('*.hsaco'));require(len(modules)==total,'extra architecture modules')
  (module_root/'SHA256SUMS').write_text(''.join(digest(f)+'  '+f.relative_to(module_root).as_posix()+'\n' for f in modules))
  require(len(list(assets.glob('*.f16')))>=50,'full network weights missing')
  defaults=stage/'DLSS5-AMD/default-config.txt';text=defaults.read_text(encoding='utf-8-sig')
  require('DLSS5_TEMPORAL_HISTORY_EXPERIMENT=0' in text and 'DLSS5_TEMPORAL_MV_UNJITTERED=0' in text,'experimental defaults must remain off/unknown')
  require(not (stage/'DLSS5-AMD/custom-config.txt').exists() and not (stage/'DLSS5-AMD/native-game-flags.txt').exists(),'package must not include player configuration')
  for name in ('temporal-history-test.ps1','TEMPORAL-HISTORY-TEST.txt'):
   require((stage/name).is_file(),'missing reviewed player test instruction '+name)
  version='OptiScaler-DLSS5-AMD-0.41-a'
  (stage/'DLSS5-AMD-VERSION.txt').write_text(version+'\nsource_commit='+payload['source_commit']+'\n')
  release={'version':'0.41-a','package':version,'kind':'optiscaler','source_commit':payload['source_commit'],
   'baseline_sha256':payload['baseline_sha256'],'modules':total,'modules_per_arch':expected,
   'regular_addon_sha256':digest(stage/'dlss5-amd.addon64'),'history_default':0,'mv_unjittered_default':0,
   'history_scope':'opt-in regular FFX pre-upscale MP1 only; no RE9/Magpie support; no depth occlusion gate',
   'flicker_fixed':False,'validation_receipts':checks,'overlay_manifest_sha256':digest(payload_file),'note':'temporary controlled history test; formal 0.41 archive is unchanged'}
  (stage/'release.json').write_text(json.dumps(release,indent=2)+'\n')
  sums=''.join(digest(p)+'  '+p.relative_to(stage).as_posix()+'\n' for p in sorted(stage.rglob('*')) if p.is_file() and p!=stage/'SHA256SUMS.txt')
  (stage/'SHA256SUMS.txt').write_text(sums);members=check_stage(stage)
  # Build and read back every member. Publication uses hard-link exclusive creation.
  partial=pathlib.Path(temp)/'package.zip'
  with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(stage.rglob('*')):
    if p.is_file():z.write(p,p.relative_to(stage).as_posix())
  with zipfile.ZipFile(partial) as z:
   require(len(z.namelist())==len(members)+1,'ZIP member count')
   for line in sums.splitlines():require(hashlib.sha256(z.read(line[66:])).hexdigest()==line[:64],'ZIP readback SHA mismatch')
  require(partial.stat().st_size>100*1024*1024,'not a full release archive')
  import os
  os.link(partial,output)
 result={'name':output.name,'bytes':output.stat().st_size,'sha256':digest(output),'files':len(members),'verified':True,'modules':total,'source_commit':payload['source_commit']}
 output.with_suffix(output.suffix+'.sha256').write_text(result['sha256']+'  '+output.name+'\n')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=pathlib.Path);p.add_argument('payload',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
 try:print(json.dumps(build(a.baseline,a.payload,a.output),indent=2))
 except (ValueError,OSError,KeyError,TypeError,zipfile.BadZipFile) as e:p.exit(1,'PACKAGE_041A_FAIL: '+str(e)+'\n')

param([switch]$ManifestOnly)
$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
$watch=[Diagnostics.Stopwatch]::StartNew()
if(!$ManifestOnly){
 & "$root\source\build-modules.ps1" -SourceDir "$root\source" -OutputDir "$root\modules-L20" -Compiler "$root\comgr2-compiler.ps1"
 if(!$?){throw 'COMGR2 build failed'}
}
$watch.Stop()
$modules=@()
foreach($arch in 'gfx1200','gfx1201'){
 $archModules=Get-Content "$root\modules-L20\$arch\modules.json" -Raw|ConvertFrom-Json
 foreach($m in $archModules){
  $modules += @{target=$arch;module=$m.module;sha256=$m.sha256.ToLower();source_sha256=(Get-FileHash "$root\modules-L20\$arch\$($m.module).generated.hip").Hash.ToLower()}
 }
}
$manifest=@{compiler='Windows COMGR2 2.9 / LLVM20 33ab2c2f7838239f1e2e5c06432bbb8d887e8cb2';seconds=$(if($ManifestOnly){$null}else{$watch.Elapsed.TotalSeconds});modules=$modules}
$manifest|ConvertTo-Json -Depth 6|Set-Content "$root\modules-L20\manifest.json"
Copy-Item "$root\modules-L20\manifest.json" "$root\manifest-L20.json"
New-Item -ItemType Directory -Force "$root\flat-L20"|Out-Null
Copy-Item "$root\modules-L20\gfx1201\*.hsaco" "$root\flat-L20"
Compress-Archive "$root\modules-L20\*" "$root\L20.zip" -Force
if($ManifestOnly){Write-Output 'Manifest rebuilt for sixty previously compiled modules; no recompilation'}
else{Write-Output "COMGR2 built sixty modules in $($watch.Elapsed.TotalSeconds) seconds"}

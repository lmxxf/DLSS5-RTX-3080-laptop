$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
$snapshot=Get-Content "$root\snapshot.json" -Raw|ConvertFrom-Json
$checked=0
foreach($f in $snapshot.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed file changed: $($f.path)"};$checked++}
$timing22=@(Get-ChildItem $root -Directory -Filter 'runtime-regression-L22-timing*').Count
if($timing22){throw 'Rejected compiler unexpectedly has timing directories'}
@{installed_files_unchanged=$checked;llvm22_timing_directories=$timing22;host_sha256=(Get-FileHash "$root\benchmark-production.exe").Hash;time=(Get-Date -Format o)}|ConvertTo-Json|Set-Content "$root\final-state.json"
Get-Content "$root\final-state.json"

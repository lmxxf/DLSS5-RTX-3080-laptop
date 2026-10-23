$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
$watch=[Diagnostics.Stopwatch]::StartNew()
& "$root\source\build-modules.ps1" -SourceDir "$root\source" -OutputDir "$root\driver" -Compiler "$root\driver-compiler.ps1"
if(!$?){throw 'Driver rebuild failed'}
$watch.Stop()
@{seconds=$watch.Elapsed.TotalSeconds;comgr=(Get-FileHash "$env:windir\System32\amd_comgr_3.dll").Hash}|ConvertTo-Json|Set-Content "$root\driver-build.json"
Compress-Archive "$root\driver\*" "$root\driver.zip" -Force

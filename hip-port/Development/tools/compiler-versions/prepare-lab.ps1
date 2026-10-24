$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
$old='D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
if(Test-Path "$root\prepared.json"){throw 'Lab already prepared; preserve snapshot'}
New-Item -ItemType Directory -Force $root|Out-Null
Copy-Item "$old\compiler-versions-source.zip" "$root\hip-source.zip"
$snapshot=Get-Content "$old\snapshot.json" -Raw|ConvertFrom-Json
foreach($f in $snapshot.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed files changed: $($f.path)"}}
Copy-Item "$old\snapshot.json","$old\base-flags.txt","$old\benchmark-production.exe","$old\regression.ps1" $root
Copy-Item "$old\baseline" "$root\baseline" -Recurse
Copy-Item "$old\flat-L" "$root\flat-L21" -Recurse
New-Item -ItemType Directory -Force "$root\flat-A"|Out-Null
Copy-Item "$old\baseline\gfx1201\*.hsaco" "$root\flat-A"
Expand-Archive "$root\hip-source.zip" "$root\source" -Force
@{time=(Get-Date -Format o);host=(Get-FileHash "$root\benchmark-production.exe").Hash;source=(Get-FileHash "$root\hip-source.zip").Hash}|ConvertTo-Json|Set-Content "$root\prepared.json"
Write-Output 'Prepared isolated lab; current game snapshot still matches.'

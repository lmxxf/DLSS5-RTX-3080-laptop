$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-patch1-20260929'
$old='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
if(Test-Path "$root\prepared.json"){throw 'Preserve existing experiment'}
New-Item -ItemType Directory -Force $root,"$root\driver\gfx1201","$root\flat-A"|Out-Null
$snap=Get-Content "$old\snapshot.json" -Raw|ConvertFrom-Json
foreach($f in $snap.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Game changed: $($f.path)"}}
Copy-Item "$old\snapshot.json","$old\base-flags.txt","$old\benchmark-production.exe","$old\regression.ps1","$old\golden.csv","$old\driver-identity-pass.json" $root
Copy-Item "$old\driver\gfx1201\modules.json" "$root\driver\gfx1201"
Copy-Item "$old\flat-A\*.hsaco" "$root\flat-A"
foreach($set in 'O','P'){
 $zip=if($set -eq 'O'){"$old\patch1-off.zip"}else{"$old\patch1-P.zip"}
 Expand-Archive $zip "$root\modules-$set" -Force
 $manifest=Get-Content "$root\modules-$set\manifest.json" -Raw|ConvertFrom-Json
 if(@($manifest.modules).Count -ne 60){throw 'Expected sixty modules'}
 foreach($m in $manifest.modules){if((Get-FileHash "$root\modules-$set\$($m.target)\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Transferred module mismatch'}}
 Copy-Item "$root\modules-$set\manifest.json" "$root\manifest-$set.json"
 New-Item -ItemType Directory -Force "$root\flat-$set"|Out-Null
 Copy-Item "$root\modules-$set\gfx1201\*.hsaco" "$root\flat-$set"
}
@{time=(Get-Date -Format o);host=(Get-FileHash "$root\benchmark-production.exe").Hash}|ConvertTo-Json|Set-Content "$root\prepared.json"
Write-Output 'Independent lab ready; game files unchanged'

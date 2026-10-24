$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
$identity=Get-Content "$root\driver-identity-pass.json" -Raw|ConvertFrom-Json
if(!$identity.pass_identity -or @($identity.modules).Count -ne 60){throw 'Driver identity gate missing'}
foreach($m in $identity.modules){if((Get-FileHash "$root\driver\$($m.target)\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Driver payload changed'}}
Copy-Item "$root\driver\gfx1201\*.hsaco" "$root\flat-A" -Force
Copy-Item "$root\new-baseline-hashes.csv" "$root\golden.csv" -Force
Copy-Item 'D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929\candidate\manifest.json' "$root\manifest-L21.json" -Force
Write-Output 'Driver baseline and public LLVM21 manifests ready'

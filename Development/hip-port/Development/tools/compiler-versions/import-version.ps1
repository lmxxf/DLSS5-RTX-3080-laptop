param([ValidateSet('L20','L21','L22')][string]$Version)
$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
if(Test-Path "$root\validation-$Version.json"){throw 'Version already tested; do not overwrite'}
Expand-Archive "$root\$Version.zip" "$root\modules-$Version" -Force
$manifest=Get-Content "$root\modules-$Version\manifest.json" -Raw|ConvertFrom-Json
if(@($manifest.modules).Count -ne 60){throw 'Expected sixty modules'}
foreach($m in $manifest.modules){if((Get-FileHash "$root\modules-$Version\$($m.target)\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Transfer mismatch'}}
New-Item -ItemType Directory -Force "$root\flat-$Version"|Out-Null
Copy-Item "$root\modules-$Version\gfx1201\*.hsaco" "$root\flat-$Version" -Force
Copy-Item "$root\modules-$Version\manifest.json" "$root\manifest-$Version.json"
Write-Output "$Version imported and sixty hashes checked"

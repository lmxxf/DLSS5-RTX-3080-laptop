$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
if(Test-Path "$root\validation-L21.json"){throw 'Do not overwrite an existing validation'}
Expand-Archive "$root\L21-evidence.zip" $root
$v=Get-Content "$root\validation-L21.json" -Raw|ConvertFrom-Json
if(!$v.pass){throw 'Reused evidence failed independent golden check'}
Write-Output 'Public LLVM21 prior regression imported with provenance; timing remains new.'

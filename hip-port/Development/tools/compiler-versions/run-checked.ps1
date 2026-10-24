param([ValidateSet('L20','L21','L22')][string]$Version)
$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
& "$root\run-version.ps1" -Version $Version -Action Regression
if(!$?){throw 'Regression execution failed'}
$v=Get-Content "$root\validation-$Version.json" -Raw|ConvertFrom-Json
if($v.pass){
 & "$root\run-version.ps1" -Version $Version -Action Timing
 if(!$?){throw 'Timing failed'}
}else{Write-Output "$Version rejected by numerical gate; no timing"}
& "$root\run-version.ps1" -Version $Version -Action Collect
if(!$?){throw 'Collect failed'}

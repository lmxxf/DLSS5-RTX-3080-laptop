$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
& "$root\run-version.ps1" -Version L21 -Action Timing
if(!$?){throw 'Public21 timing failed'}
& "$root\run-version.ps1" -Version L21 -Action Collect
if(!$?){throw 'Public21 collection failed'}
& "$root\run-checked.ps1" -Version L22
if(!$?){throw 'LLVM22 comparison failed'}

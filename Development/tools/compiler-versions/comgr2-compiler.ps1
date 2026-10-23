param([string]$Output,[string]$Source,[string]$Backend,[string]$Target)
$ErrorActionPreference='Stop'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
& 'D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929\rtc_compile-comgr2.exe' $Output $Source $Backend $Target
if($LASTEXITCODE){throw "COMGR2 compile failed $Source"}
$global:LASTEXITCODE=0

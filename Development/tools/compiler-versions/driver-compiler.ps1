param([string]$Output,[string]$Source,[string]$Backend,[string]$Target)
$ErrorActionPreference='Stop'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
& 'D:\DLSSNR-Lab\build-0927\rtc_compile.exe' $Output $Source $Backend $Target
if($LASTEXITCODE){throw "Driver compile failed $Source"}
$global:LASTEXITCODE=0

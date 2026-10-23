# Full 24-module build with extra compiler options (RTC_EXTRA_OPTS) into hip-backend\opt-<name>-modules.
param([Parameter(Mandatory=$true)][string]$Name,[string]$Opts='')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$env:RTC_EXTRA_OPTS=$Opts
& "$r\build-modules.ps1" -Compiler "$r\rtc_compile_opts.exe" -OutputDir "$r\opt-$Name-modules" -SourceDir "$r\src-opt" -IsaHalf -Fast
if($LASTEXITCODE){throw "build failed $Name"}
Get-ChildItem "$r\opt-$Name-modules\*.hsaco" | Measure-Object | ForEach-Object { Write-Output "modules=$($_.Count) name=$Name opts=[$Opts]" }

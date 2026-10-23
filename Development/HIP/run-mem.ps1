param([string]$Runner='benchmark_mem.exe',[string]$Modules='ffnh2-modules',[string]$FlagsBase='vitcf-on-flags.txt',[string]$Extra='DLSS5_HIP_MEMORY=1')
# Runs a 4-frame bench with DLSS5_HIP_MEMORY=1 and prints the device memory breakdown the runner appended to logs\native-hip.txt.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\$FlagsBase");$keys=@($Extra.Split(';')|ForEach-Object{$_.Split('=')[0]})
@($base|Where-Object{$k=$_.Split('=')[0];$keys -notcontains $k})+@($Extra.Split(';'))|Set-Content "$r\mem-flags.txt"
$logs=Get-ChildItem -Path $r,"$r\.." -Recurse -Filter native-hip.txt -ErrorAction SilentlyContinue|ForEach-Object{$_.FullName}
foreach($l in $logs){Clear-Content $l -ErrorAction SilentlyContinue}
& "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name mem-run -Flags mem-flags.txt -Frames 4
$logs=Get-ChildItem -Path $r,"$r\.." -Recurse -Filter native-hip.txt -ErrorAction SilentlyContinue|ForEach-Object{$_.FullName}
foreach($l in $logs){Write-Output "== $l";Get-Content $l|Select-String 'hip_memory'}

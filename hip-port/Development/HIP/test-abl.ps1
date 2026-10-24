param([string]$Candidate='c32-bf',[string]$Base='vitcf')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($i in 0..3){
 $m=if($i -in @(1,2)){"$Candidate-modules"}else{"$Base-modules"}
 Write-Output "ROUND=$i modules=$m"
 & "$r\validate-hdr.ps1" -Runner benchmark_vitcf.exe -Modules $m -Name "$Candidate-$i" -Flags vitcf-on-flags.txt -EdgesOnly 1
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

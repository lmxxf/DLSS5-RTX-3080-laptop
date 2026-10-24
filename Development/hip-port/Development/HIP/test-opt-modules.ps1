# ABBA: opt-base-modules (same compiler, no extra opts) vs opt-<Name>-modules; production flags; hash must match.
param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($i in 0..3){
 $m=if($i -in @(1,2)){"opt-$Name-modules"}else{'opt-base-modules'}
 Write-Output "ROUND=$i modules=$m"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_hstream.exe -Modules $m -Name "opt-$Name-$i" -Flags vit-all-on-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

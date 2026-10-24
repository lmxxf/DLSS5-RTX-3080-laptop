$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($i in 0..3){
 $m=if($i -in @(1,2)){'c32-occ12-modules'}else{'c32-lane-modules'}
 Write-Output "ROUND=$i modules=$m"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_ffn.exe -Modules $m -Name "c32-occ12-$i" -Flags vit-all-on-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($job in @(@('default','vit-all-on-flags.txt'),@('explicit','c512-frag-on-flags.txt'),@('default2','vit-all-on-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_c512_pfrag.exe -Modules c512-pfrag-modules -Name "c512-fragdef-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
}

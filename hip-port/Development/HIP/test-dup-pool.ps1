$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
($base+@('DLSS5_HIP_DUP_PREFIX=mh_pool$'))|Set-Content "$r\dup-poolx-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=mh_pool_project_production$'))|Set-Content "$r\dup-poolproj-flags.txt"
foreach($job in @(@(0,'dup-none-flags.txt'),@(1,'dup-poolx-flags.txt'),@(2,'dup-poolproj-flags.txt'),@(3,'dup-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_dupp.exe -Modules opt-base-modules -Name "dupp-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

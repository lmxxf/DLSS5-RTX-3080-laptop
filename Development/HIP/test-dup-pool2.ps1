$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\pool-project-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
$base|Set-Content "$r\dupp2-none-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=mh_pool_project_fused_c64$'))|Set-Content "$r\dupp2-f64-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=mh_pool_project_production$'))|Set-Content "$r\dupp2-prod-flags.txt"
foreach($job in @(@(0,'dupp2-none-flags.txt'),@(1,'dupp2-f64-flags.txt'),@(2,'dupp2-prod-flags.txt'),@(3,'dupp2-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_pool_project.exe -Modules pool-project-modules -Name "dupp2-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

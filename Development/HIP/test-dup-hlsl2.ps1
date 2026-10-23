$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_DUP_BLOCKS='})
($base+@('DLSS5_DUP_BLOCKS=9,10,11,12,13,14,56,57,58,59,60,61'))|Set-Content "$r\duph-c128-flags.txt"
($base+@('DLSS5_DUP_BLOCKS=31,32,33,34,35,36,37,38'))|Set-Content "$r\duph-vit-flags.txt"
foreach($job in @(@(0,'duph-none-flags.txt'),@(1,'duph-c128-flags.txt'),@(2,'duph-vit-flags.txt'),@(3,'duph-none-flags.txt'),@(4,'duph-c128-flags.txt'),@(5,'duph-vit-flags.txt'),@(6,'duph-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_hlsl_dup.exe -Modules opt-base-modules -Name "duph2-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

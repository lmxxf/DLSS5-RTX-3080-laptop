# HLSL twin of test-dup-launch.ps1: record the C64 / C256 blocks twice and read the frame delta (identical output).
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_DUP_BLOCKS='})
$base|Set-Content "$r\duph-none-flags.txt"
($base+@('DLSS5_DUP_BLOCKS=5,6,7,8,62,63,64,65'))|Set-Content "$r\duph-c64-flags.txt"
($base+@('DLSS5_DUP_BLOCKS=15,16,17,18,19,20,21,22,48,49,50,51,52,53,54,55'))|Set-Content "$r\duph-c256-flags.txt"
foreach($job in @(@(0,'duph-none-flags.txt'),@(1,'duph-c64-flags.txt'),@(2,'duph-c256-flags.txt'),@(3,'duph-none-flags.txt'),@(4,'duph-c64-flags.txt'),@(5,'duph-c256-flags.txt'),@(6,'duph-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_hlsl_dup.exe -Modules opt-base-modules -Name "duph-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

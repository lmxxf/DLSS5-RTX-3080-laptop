$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_DUP_BLOCKS='})
($base+@('DLSS5_DUP_BLOCKS=70'))|Set-Content "$r\duph-post-flags.txt"
($base+@('DLSS5_DUP_BLOCKS=0'))|Set-Content "$r\duph-pre-flags.txt"
($base+@('DLSS5_DUP_BLOCKS=104,108,114,122'))|Set-Content "$r\duph-ds-flags.txt"
foreach($job in @(@(0,'duph-none-flags.txt'),@(1,'duph-post-flags.txt'),@(2,'duph-pre-flags.txt'),@(3,'duph-ds-flags.txt'),@(4,'duph-post-flags.txt'),@(5,'duph-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_hlsl_dup.exe -Modules opt-base-modules -Name "duph5-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

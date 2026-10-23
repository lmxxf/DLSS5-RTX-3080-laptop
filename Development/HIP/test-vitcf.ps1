$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_CONTRACT_FRAG='})
($base+@('DLSS5_HIP_VIT_CONTRACT_FRAG=0'))|Set-Content "$r\vitcf-off-flags.txt"
($base+@('DLSS5_HIP_VIT_CONTRACT_FRAG=1'))|Set-Content "$r\vitcf-on-flags.txt"
& "$r\test_vit_linear_frag.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vitcf-modules"
if($LASTEXITCODE){throw 'vit contract frag mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'vitcf-on-flags.txt'}else{'vitcf-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vitcf.exe -Modules vitcf-modules -Name "vitcf-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

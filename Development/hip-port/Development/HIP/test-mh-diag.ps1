$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_MH_PROJ_DIAG='})
($base+@('DLSS5_HIP_MH_PROJ_DIAG=0'))|Set-Content "$r\mh-diag-off-flags.txt"
($base+@('DLSS5_HIP_MH_PROJ_DIAG=1'))|Set-Content "$r\mh-diag-on-flags.txt"
& "$r\test_mh_proj_diag.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\mh-diag-modules"
if($LASTEXITCODE){throw 'mh proj diag mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'mh-diag-on-flags.txt'}else{'mh-diag-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_mh_diag.exe -Modules mh-diag-modules -Name "mh-diag-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

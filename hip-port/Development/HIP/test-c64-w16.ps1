$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_MH_ATTN_W16='})
($base+@('DLSS5_HIP_MH_ATTN_W16=0'))|Set-Content "$r\c64-w16-off-flags.txt"
($base+@('DLSS5_HIP_MH_ATTN_W16=1'))|Set-Content "$r\c64-w16-on-flags.txt"
& "$r\test_c64_attn_w16.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\c64-w16-modules"
if($LASTEXITCODE){throw 'c64 w16 mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'c64-w16-on-flags.txt'}else{'c64-w16-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_c64_w16.exe -Modules c64-w16-modules -Name "c64-w16-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_TILED_FFN_SMALL='})
($base+@('DLSS5_HIP_TILED_FFN_SMALL=0'))|Set-Content "$r\tsmall-off-flags.txt"
($base+@('DLSS5_HIP_TILED_FFN_SMALL=1'))|Set-Content "$r\tsmall-on-flags.txt"
& "$r\test_ffn_tiled_small.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\tsmall-modules"
if($LASTEXITCODE){throw 'tiled small mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'tsmall-on-flags.txt'}else{'tsmall-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_tsmall.exe -Modules tsmall-modules -Name "tsmall-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

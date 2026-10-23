$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_SPLIT_MIX_H16W='})
($base+@('DLSS5_HIP_SPLIT_MIX_H16W=0'))|Set-Content "$r\c512-mixw-off-flags.txt"
($base+@('DLSS5_HIP_SPLIT_MIX_H16W=1'))|Set-Content "$r\c512-mixw-on-flags.txt"
& "$r\test_split_mix_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\c512-mixw-modules"
if($LASTEXITCODE){throw 'split mix fused mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'c512-mixw-on-flags.txt'}else{'c512-mixw-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_c512_mixw.exe -Modules c512-mixw-modules -Name "c512-mixw-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

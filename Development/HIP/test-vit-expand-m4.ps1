$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-fp8-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_EXPAND_M4='})
($base+@('DLSS5_HIP_VIT_EXPAND_M4=0'))|Set-Content "$r\vit-expand-m4-off-flags.txt"
($base+@('DLSS5_HIP_VIT_EXPAND_M4=1'))|Set-Content "$r\vit-expand-m4-on-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-expand-m4-modules"
if($LASTEXITCODE){throw 'expand m4 mismatch'}
foreach($i in 0..3){
 $on=$i -in @(1,2)
 $modules=if($on){'vit-expand-m4-modules'}else{'vit-qkv-fp8-modules'}
 $flags=if($on){'vit-expand-m4-on-flags.txt'}else{'vit-expand-m4-off-flags.txt'}
 Write-Output "ROUND=$i modules=$modules flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_expand_m4.exe -Modules $modules -Name "vit-expand-m4-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

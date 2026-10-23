$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-fp8-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_EXPAND_M4=|^DLSS5_HIP_VIT_EXPAND_FRAG='})
($base+@('DLSS5_HIP_VIT_EXPAND_M4=0','DLSS5_HIP_VIT_EXPAND_FRAG=0'))|Set-Content "$r\vit-expand-fm4-off-flags.txt"
($base+@('DLSS5_HIP_VIT_EXPAND_M4=1','DLSS5_HIP_VIT_EXPAND_FRAG=0'))|Set-Content "$r\vit-expand-m4u-on-flags.txt"
($base+@('DLSS5_HIP_VIT_EXPAND_M4=1','DLSS5_HIP_VIT_EXPAND_FRAG=1'))|Set-Content "$r\vit-expand-fm4-on-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-expand-fm4-modules"
if($LASTEXITCODE){throw 'expand mismatch'}
foreach($job in @(@(0,'vit-qkv-fp8-modules','vit-expand-fm4-off-flags.txt'),@(1,'vit-expand-fm4-modules','vit-expand-m4u-on-flags.txt'),@(2,'vit-expand-fm4-modules','vit-expand-fm4-on-flags.txt'),@(3,'vit-expand-fm4-modules','vit-expand-fm4-on-flags.txt'),@(4,'vit-expand-fm4-modules','vit-expand-m4u-on-flags.txt'),@(5,'vit-qkv-fp8-modules','vit-expand-fm4-off-flags.txt'))){
 Write-Output "ROUND=$($job[0]) modules=$($job[1]) flags=$($job[2])"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_expand_frag.exe -Modules $job[1] -Name "vit-expand-fm4-$($job[0])" -Flags $job[2] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

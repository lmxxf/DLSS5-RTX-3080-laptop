$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-validation-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_ATTN_FUSED='})
($base+@('DLSS5_HIP_VIT_ATTN_FUSED=0'))|Set-Content "$r\vit-attn-fused-off-flags.txt"
($base+@('DLSS5_HIP_VIT_ATTN_FUSED=1'))|Set-Content "$r\vit-attn-fused-on-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-attn-fused-modules"
if($LASTEXITCODE){throw 'fused attention mismatch'}
foreach($i in 0..3){
 $on=$i -in @(1,2)
 $modules=if($on){'vit-attn-fused-modules'}else{'ffn-qkv-round-byte-release-modules'}
 $flags=if($on){'vit-attn-fused-on-flags.txt'}else{'vit-attn-fused-off-flags.txt'}
 Write-Output "ROUND=$i modules=$modules flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_attn_fused.exe -Modules $modules -Name "vit-attn-fused-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

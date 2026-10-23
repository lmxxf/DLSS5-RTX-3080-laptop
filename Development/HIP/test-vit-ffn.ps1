$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_FFN_FUSED='})
($base+@('DLSS5_HIP_VIT_FFN_FUSED=0'))|Set-Content "$r\vit-ffn-off-flags.txt"
($base+@('DLSS5_HIP_VIT_FFN_FUSED=1'))|Set-Content "$r\vit-ffn-on-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-ffn-modules"
if($LASTEXITCODE){throw 'vit m2 mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'vit-ffn-on-flags.txt'}else{'vit-ffn-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_ffn.exe -Modules vit-ffn-modules -Name "vit-ffn-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_FFN_QKV_BN='})
($base+@('DLSS5_HIP_FFN_QKV_BN=0'))|Set-Content "$r\ffn-qkv-bn-off-flags.txt"
($base+@('DLSS5_HIP_FFN_QKV_BN=1'))|Set-Content "$r\ffn-qkv-bn-on-flags.txt"
& "$r\test_ffn_qkv_bn.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\ffn-qkv-bn-modules"
if($LASTEXITCODE){throw 'batched norm mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'ffn-qkv-bn-on-flags.txt'}else{'ffn-qkv-bn-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_ffn_qkv_bn.exe -Modules ffn-qkv-bn-modules -Name "ffn-qkv-bn-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

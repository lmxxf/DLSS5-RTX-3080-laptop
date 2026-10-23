$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_BYTE_STREAM=|^DLSS5_HIP_VIT_HALF_STREAM=|^DLSS5_HIP_VIT_QKV_N4='})
($base+@('DLSS5_HIP_VIT_BYTE_STREAM=0','DLSS5_HIP_VIT_HALF_STREAM=0','DLSS5_HIP_VIT_QKV_N4=0'))|Set-Content "$r\vit-half-stream-off-flags.txt"
($base+@('DLSS5_HIP_VIT_BYTE_STREAM=1','DLSS5_HIP_VIT_HALF_STREAM=1','DLSS5_HIP_VIT_QKV_N4=0'))|Set-Content "$r\vit-half-stream-n2-flags.txt"
($base+@('DLSS5_HIP_VIT_BYTE_STREAM=1','DLSS5_HIP_VIT_HALF_STREAM=1','DLSS5_HIP_VIT_QKV_N4=1'))|Set-Content "$r\vit-half-stream-n4-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-half-stream-modules"
if($LASTEXITCODE){throw 'half stream mismatch'}
foreach($job in @(@(0,'vit-half-stream-off-flags.txt'),@(1,'vit-half-stream-n2-flags.txt'),@(2,'vit-half-stream-n4-flags.txt'),@(3,'vit-half-stream-n4-flags.txt'),@(4,'vit-half-stream-n2-flags.txt'),@(5,'vit-half-stream-off-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_hstream.exe -Modules vit-half-stream-modules -Name "vit-half-stream-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

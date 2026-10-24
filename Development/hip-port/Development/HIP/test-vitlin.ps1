$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_PROJ_FRAG=|^DLSS5_HIP_VIT_QKV_FRAG='})
($base+@('DLSS5_HIP_VIT_PROJ_FRAG=0','DLSS5_HIP_VIT_QKV_FRAG=0'))|Set-Content "$r\vitlin-off-flags.txt"
($base+@('DLSS5_HIP_VIT_PROJ_FRAG=1','DLSS5_HIP_VIT_QKV_FRAG=0'))|Set-Content "$r\vitlin-proj-flags.txt"
($base+@('DLSS5_HIP_VIT_PROJ_FRAG=0','DLSS5_HIP_VIT_QKV_FRAG=1'))|Set-Content "$r\vitlin-qkv-flags.txt"
($base+@('DLSS5_HIP_VIT_PROJ_FRAG=1','DLSS5_HIP_VIT_QKV_FRAG=1'))|Set-Content "$r\vitlin-on-flags.txt"
& "$r\test_vit_linear_frag.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vitlin-modules"
if($LASTEXITCODE){throw 'vit linear frag mismatch'}
$jobs=@('off','proj','qkv','on','off','on')
$i=0;foreach($k in $jobs){
 Write-Output "ROUND=$k"
 & "$r\validate-hdr.ps1" -Runner benchmark_vitlin.exe -Modules vitlin-modules -Name "vitlin-$i-$k" -Flags "vitlin-$k-flags.txt" -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 $i++
}

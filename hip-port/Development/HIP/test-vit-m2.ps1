$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_EXPAND_M2='})
($base+@('DLSS5_HIP_VIT_EXPAND_M2=0'))|Set-Content "$r\vit-m2-off-flags.txt"
($base+@('DLSS5_HIP_VIT_EXPAND_M2=1'))|Set-Content "$r\vit-m2-on-flags.txt"
& "$r\test_vit_attn_fused.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\vit-m2-modules"
if($LASTEXITCODE){throw 'vit m2 mismatch'}
Select-String -Path "$r\vit-m2.hsaco.s" -Pattern 'frag_bytein_m2$' -Context 0,0 | Out-Null
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'vit-m2-on-flags.txt'}else{'vit-m2-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_m2.exe -Modules vit-m2-modules -Name "vit-m2-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

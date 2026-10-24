$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_POOL_PROJECT_GROUP='})
($base+@('DLSS5_HIP_POOL_PROJECT_GROUP=0'))|Set-Content "$r\poolg-off-flags.txt"
($base+@('DLSS5_HIP_POOL_PROJECT_GROUP=1'))|Set-Content "$r\poolg-on-flags.txt"
& "$r\test_pool_group.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\poolg-modules"
if($LASTEXITCODE){throw 'pool group mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'poolg-on-flags.txt'}else{'poolg-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_poolg.exe -Modules poolg-modules -Name "poolg-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

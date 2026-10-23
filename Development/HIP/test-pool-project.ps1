$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_POOL_PROJECT_FUSED='})
($base+@('DLSS5_HIP_POOL_PROJECT_FUSED=0'))|Set-Content "$r\pool-project-off-flags.txt"
($base+@('DLSS5_HIP_POOL_PROJECT_FUSED=1'))|Set-Content "$r\pool-project-on-flags.txt"
& "$r\test_pool_project.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\pool-project-modules"
if($LASTEXITCODE){throw 'pool project mismatch'}
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'pool-project-on-flags.txt'}else{'pool-project-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_pool_project.exe -Modules pool-project-modules -Name "pool-project-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

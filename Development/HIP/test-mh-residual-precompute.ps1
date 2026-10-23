$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-residual-precompute-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-global-ffn-release-modules\*.hsaco" $m -Force
Copy-Item "$r\mh-residual-precompute.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
$lines=@(Get-Content "$r\vit-qkv-validation-flags.txt")
$lines|Set-Content "$r\mh-residual-precompute-flags.txt"
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){'mh-residual-precompute-modules'}else{'c32-global-ffn-release-modules'}
 $runner=if($i -in @(1,2)){'benchmark_mh_residual_precompute.exe'}else{'benchmark_vit_qkv_fused.exe'}
 Write-Output "ROUND=$i modules=$modules"
 & "$r\validate-hdr.ps1" -Runner $runner -Modules $modules -Name "mh-residual-precompute-$i" -Flags mh-residual-precompute-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-av-pair-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\vit-qkv-fused-release-modules\*.hsaco" $m -Force
Copy-Item "$r\mh-av-pair.hsaco" "$m\multihead_fused_attention.hsaco" -Force
$lines=@(Get-Content "$r\vit-qkv-validation-flags.txt")
$lines|Set-Content "$r\mh-av-pair-flags.txt"
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){'mh-av-pair-modules'}else{'vit-qkv-fused-release-modules'}
 Write-Output "ROUND=$i modules=$modules"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_qkv_fused.exe -Modules $modules -Name "mh-av-pair-$i" -Flags mh-av-pair-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

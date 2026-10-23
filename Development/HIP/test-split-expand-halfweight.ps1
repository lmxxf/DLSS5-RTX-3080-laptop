$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\split-expand-halfweight-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\vit-qkv-halfweight-release-modules\*.hsaco" $m -Force
Copy-Item "$r\split-expand-halfweight.hsaco" "$m\deep_fast-packed.hsaco" -Force
$lines=@(Get-Content "$r\vit-qkv-validation-flags.txt")
$lines|Set-Content "$r\split-expand-halfweight-flags.txt"
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){'split-expand-halfweight-modules'}else{'vit-qkv-halfweight-release-modules'}
 $runner=if($i -in @(1,2)){'benchmark_split_expand_halfweight.exe'}else{'benchmark_vit_qkv_halfweight.exe'}
 Write-Output "ROUND=$i modules=$modules"
 & "$r\validate-hdr.ps1" -Runner $runner -Modules $modules -Name "split-expand-halfweight-$i" -Flags split-expand-halfweight-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

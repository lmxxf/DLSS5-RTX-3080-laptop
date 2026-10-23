$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\dense-direct-fbyte-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffn-input-pack4-release-modules\*.hsaco" $m -Force
foreach($i in 0..3){
 $candidate=$i -in @(1,2)
 $src=if($candidate){"$r\dense-direct-fbyte.hsaco"}else{"$r\ffn-input-pack4-release-modules\multihead-fast-padded-wave-packed.hsaco"}
 Copy-Item $src "$m\multihead-fast-padded-wave-packed.hsaco" -Force
 Write-Output "ROUND=$i candidate=$candidate"
 & "$r\validate-hdr.ps1" -Runner benchmark_hip_edges.exe -Modules dense-direct-fbyte-modules -Name "dense-direct-fbyte-$i" -Flags rebind-async-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

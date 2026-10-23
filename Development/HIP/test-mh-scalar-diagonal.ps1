$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-scalar-diagonal-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-alias-ffn-release-modules\*.hsaco" $m -Force
foreach($i in 0..3){
 $candidate=$i -in @(1,2);$enabled=1
 $src=if($candidate){"$r\mh-scalar-diagonal.hsaco"}else{"$r\c32-alias-ffn-release-modules\multihead-fast-padded-wave-packed.hsaco"}
 Copy-Item $src "$m\multihead-fast-padded-wave-packed.hsaco" -Force
 $lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_PREFIX_FUSED='});$lines+="DLSS5_HIP_PREFIX_FUSED=$enabled";$lines|Set-Content "$r\prefix-fused-flags.txt"
 Write-Output "ROUND=$i candidate=$candidate"
 & "$r\validate-hdr.ps1" -Runner benchmark_prefix_fused.exe -Modules mh-scalar-diagonal-modules -Name "mh-scalar-diagonal-$i" -Flags prefix-fused-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\prefix-inline-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\prefix-fused-release-modules\*.hsaco" $m -Force
foreach($i in 0..3){
 $candidate=$i -in @(1,2);$enabled=if($candidate){1}else{0}
 $src=if($candidate){"$r\prefix-inline.hsaco"}else{"$r\prefix-fused-release-modules\c32_fused_ffn_attention-packed.hsaco"}
 Copy-Item $src "$m\c32_fused_ffn_attention-packed.hsaco" -Force
 $lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_PREFIX_INLINE='});$lines+="DLSS5_HIP_PREFIX_INLINE=$enabled";$lines+="DLSS5_HIP_PREFIX_FUSED=1";$lines|Set-Content "$r\prefix-inline-flags.txt"
 Write-Output "ROUND=$i candidate=$candidate"
 & "$r\validate-hdr.ps1" -Runner benchmark_prefix_inline.exe -Modules prefix-inline-modules -Name "prefix-inline-$i" -Flags prefix-inline-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

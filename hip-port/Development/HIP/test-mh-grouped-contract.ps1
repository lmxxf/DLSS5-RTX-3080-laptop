$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-grouped-contract-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\prefix-direct-input-release-modules\*.hsaco" $m -Force
foreach($i in 0..3){
 $candidate=$i -in @(1,2);$enabled=if($candidate){1}else{0}
 $src=if($candidate){"$r\mh-grouped-contract.hsaco"}else{"$r\prefix-direct-input-release-modules\multihead-fast-padded-wave-packed.hsaco"}
 Copy-Item $src "$m\multihead-fast-padded-wave-packed.hsaco" -Force
 $lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_GROUPED_CONTRACT='});$lines+="DLSS5_HIP_GROUPED_CONTRACT=$enabled";$lines+=@("DLSS5_HIP_PREFIX_FUSED=1","DLSS5_HIP_DIRECT_INPUT=1");$lines|Set-Content "$r\mh-grouped-contract-flags.txt"
 Write-Output "ROUND=$i candidate=$candidate"
 & "$r\validate-hdr.ps1" -Runner benchmark_grouped_contract.exe -Modules mh-grouped-contract-modules -Name "mh-grouped-contract-$i" -Flags mh-grouped-contract-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

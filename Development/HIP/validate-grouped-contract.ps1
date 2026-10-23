$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
Copy-Item "$r\mh-grouped-contract.hsaco" "$r\mh-grouped-contract-modules\multihead-fast-padded-wave-packed.hsaco" -Force
$lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_GROUPED_CONTRACT=|^DLSS5_HIP_PREFIX_FUSED=|^DLSS5_HIP_DIRECT_INPUT='})
$lines+=@('DLSS5_HIP_GROUPED_CONTRACT=1','DLSS5_HIP_PREFIX_FUSED=1','DLSS5_HIP_DIRECT_INPUT=1');$lines|Set-Content "$r\mh-grouped-contract-flags.txt"
& "$r\validate-hdr.ps1" -Runner benchmark_grouped_contract.exe -Modules mh-grouped-contract-modules -Name grouped-contract-full -Flags mh-grouped-contract-flags.txt -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
& "$r\validate-hdr.ps1" -Runner benchmark_grouped_contract.exe -Modules mh-grouped-contract-modules -Name grouped-contract-reset -Flags mh-grouped-contract-flags.txt -Frames 24 -ResetEvery 8 -ExpectedHash 22C171FCE0AA2DF325D3CEB65A7A1C3FFEFB56821B65A0834680506E9D05AFC8
& "$r\validate-grouped-history.ps1" | Select-String 'iteration=|reference complete'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}

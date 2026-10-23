$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
Copy-Item "$r\prefix-direct-input.hsaco" "$r\prefix-direct-input-modules\prefix_fast.hsaco" -Force
$lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DIRECT_INPUT=|^DLSS5_HIP_PREFIX_FUSED='})
$lines+=@('DLSS5_HIP_DIRECT_INPUT=1','DLSS5_HIP_PREFIX_FUSED=1');$lines|Set-Content "$r\prefix-direct-input-flags.txt"
& "$r\validate-hdr.ps1" -Runner benchmark_direct_input.exe -Modules prefix-direct-input-modules -Name direct-input-full -Flags prefix-direct-input-flags.txt -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
& "$r\validate-hdr.ps1" -Runner benchmark_direct_input.exe -Modules prefix-direct-input-modules -Name direct-input-reset -Flags prefix-direct-input-flags.txt -Frames 24 -ResetEvery 8 -ExpectedHash 22C171FCE0AA2DF325D3CEB65A7A1C3FFEFB56821B65A0834680506E9D05AFC8
foreach($case in @(@('rotate',1,2),@('evict',2,3))){
 $name='direct-input-'+$case[0]
 & "$r\run-queued-frame.ps1" -Runner queued_direct_input.exe -Flags prefix-direct-input-flags.txt -Modules prefix-direct-input-modules -Name $name -Async 1 -Rotate $case[1] -Temporal $case[2] | Out-Null
 if((Get-FileHash "$r\$name.f16").Hash -ne '43712DDEE8EA04AD645BB2A1AEC55F60839F27C0C3E293A94DC2A5EC35399DFF'){throw "Queued mismatch $name"}
 Write-Output "PASS all-frame $name"
}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}

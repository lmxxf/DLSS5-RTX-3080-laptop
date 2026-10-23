$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\check_event_timing.exe" "$r\ffn-qkv-round-byte-release-modules\deep_fast-packed.hsaco"
$status=$LASTEXITCODE
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard timings'}
if($status -gt 1){throw 'Probe failed before measurement'}
Write-Output "PROBE_EXIT=$status"

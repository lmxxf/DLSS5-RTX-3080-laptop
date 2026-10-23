$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\compare_layers_current.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\hlsl-0-flags.txt" "$r\ffn-qkv-round-byte-release-modules" "$r\mh-current-latest.csv" 1 fused-selected mh-only > "$r\mh-current-latest.log"
if($LASTEXITCODE){throw 'Comparison failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
Get-Content "$r\mh-current-latest.log" | Select-String 'CHECK|PATH|TIME|HIP_KERNEL_BATCH|network_gpu_interval'

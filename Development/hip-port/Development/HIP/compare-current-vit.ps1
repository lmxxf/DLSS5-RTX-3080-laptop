$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\compare_layers_all.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\hlsl-0-flags.txt" "$r\ffn-qkv-round-byte-release-modules" "$r\vit-current-latest.csv" 1 fused-selected vit-only > "$r\vit-current-latest.log"
if($LASTEXITCODE){throw 'Comparison failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
Get-Content "$r\vit-current-latest.log" | Select-String 'CHECK|PATH|TIME|HIP_KERNEL_BATCH|network_gpu_interval'

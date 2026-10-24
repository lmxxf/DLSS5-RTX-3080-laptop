$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\compare_layers_all.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\hlsl-0-attn-flags.txt" "$r\vit-attn-fused-modules" "$r\vit-attn-latest.csv" 1 fused-selected vit-only > "$r\vit-attn-latest.log"
if($LASTEXITCODE){throw 'Comparison failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
Get-Content "$r\vit-attn-latest.log" | Select-String 'CHECK|PATH|TIME|HIP_KERNEL_BATCH|network_gpu_interval'

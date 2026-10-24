param([int]$Pattern=1)
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Close Stellar Blade before isolated GPU comparison.'}
$r='D:\DLSSNR-Lab\hip-backend'
& "$r\compare_layers.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\hlsl-0-flags.txt" "$r\qkv-modules" "$r\layers-final-p$Pattern.csv" $Pattern > "$r\layers-final-p$Pattern.log"
if($LASTEXITCODE){Get-Content "$r\layers-final-p$Pattern.log" -Tail 20;throw 'Layer comparison failed'}
Get-Content "$r\layers-final-p$Pattern.log"|Select-String 'CHECK|PATH|TIME|HIP_KERNEL_BATCH'

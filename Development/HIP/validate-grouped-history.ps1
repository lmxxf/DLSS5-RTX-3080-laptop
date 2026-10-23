$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\reference_current.exe" $a "$r\mh-grouped-contract-modules" "$r\input900.rgba32f" "$a\noise.f32" "$r\grouped-history-check.f32" --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --packed-c32 --fp8-normalized --fp8-ffn --fp8-av --fp8-deep --fp8-middle --half-c32 --crop-c32 --fused-qkv-norm --fused-mh-ffn --tiled-mh-ffn-large --mapped-c32 --vit-blocked --vit-contract-blocked --vit-weight-mask 1 --vit-pack-input --elide-identity-shift --raw-chain --pre-main8 --post-merge-fold --fused-ffn-project --split-ffn-fused --split-mix-blocked --split-project-blocked --vit-qkv-blocked --mh-project-crop --mh-input-mapped --prefix-fused --direct-prefix-input --grouped-mh-contract --seed 123 --history "$r\input900.rgba32f" --repeat 2 > "$r\grouped-history-check.log"
if($LASTEXITCODE){throw 'Profile failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard timings'}
if((Get-FileHash "$r\grouped-history-check.f32").Hash -ne '75B62D2F36B6861B1536EC06B087C3DDB8850F4CDF810E734E16E2BC0223C3F8'){throw 'Output mismatch'}
Get-Content "$r\grouped-history-check.log"

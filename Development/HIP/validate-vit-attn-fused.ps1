$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\validate-hdr.ps1" -Runner benchmark_vit_attn_fused.exe -Modules vit-attn-fused-modules -Name vit-attn-fused-full -Flags vit-attn-fused-on-flags.txt -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
& "$r\validate-hdr.ps1" -Runner benchmark_vit_attn_fused.exe -Modules vit-attn-fused-modules -Name vit-attn-fused-reset -Flags vit-attn-fused-on-flags.txt -Frames 24 -ResetEvery 8 -ExpectedHash 22C171FCE0AA2DF325D3CEB65A7A1C3FFEFB56821B65A0834680506E9D05AFC8
& "$r\reference_vitattn.exe" $a "$r\vit-attn-fused-modules" "$r\input900.rgba32f" "$a\noise.f32" "$r\vit-attn-fused-history-check.f32" --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --packed-c32 --fp8-normalized --fp8-ffn --fp8-av --fp8-deep --fp8-middle --half-c32 --crop-c32 --fused-qkv-norm --fused-mh-ffn --tiled-mh-ffn-large --mapped-c32 --vit-blocked --vit-contract-blocked --vit-weight-mask 1 --vit-pack-input --elide-identity-shift --raw-chain --pre-main8 --post-merge-fold --fused-ffn-project --split-ffn-fused --split-mix-blocked --split-project-blocked --vit-qkv-blocked --mh-project-crop --mh-input-mapped --prefix-fused --direct-prefix-input --grouped-mh-contract --ffn-qkv --ffn-qkv-max-c 256 --vit-qkv-fused --vit-attn-fused --seed 123 --history "$r\input900.rgba32f" --repeat 2 > "$r\vit-attn-fused-history-check.log"
if($LASTEXITCODE){throw 'history reference failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard timings'}
$h=(Get-FileHash "$r\vit-attn-fused-history-check.f32").Hash
if($h -ne '75B62D2F36B6861B1536EC06B087C3DDB8850F4CDF810E734E16E2BC0223C3F8'){throw "history output mismatch $h"}
Write-Output "history seed123 hash=$h"
Get-Content "$r\vit-attn-fused-history-check.log" | Select-String 'iteration=|reference complete'

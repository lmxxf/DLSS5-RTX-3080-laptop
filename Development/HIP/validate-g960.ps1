param([string]$Modules='ffnh2-modules')
# 900s geometry (1600x900 padded to 960 rows): timing ABBA against the 1024-row production geometry (no hash gate: the output legitimately changes),
# then the three outputs for a PSNR comparison against the 1024-row golden outputs (full/reset via the HDR bench, seed-123 history via the reference chain).
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
& "$r\test-flag-ab.ps1" -Modules $Modules -Runner benchmark_g960.exe -Extra 'DLSS5_NETWORK_HEIGHT=900s' -Tag g960 -CheckHash 0
$base=@(Get-Content "$r\vitcf-on-flags.txt" | Where-Object {$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900s');$base | Set-Content "$r\g960-flags.txt"
& "$r\validate-hdr.ps1" -Runner benchmark_g960.exe -Modules $Modules -Name g960-p-full -Flags g960-flags.txt
& "$r\validate-hdr.ps1" -Runner benchmark_g960.exe -Modules $Modules -Name g960-p-reset -Flags g960-flags.txt -Frames 24 -ResetEvery 8
$ref=@("$a","$r\$Modules","$r\input960.rgba32f","$a\noise.f32","$r\g960-history.f32",'--960','--wmma','--wave','--tiled','--pooled','--fused-c32','--fused-ffn','--fused-mh','--fast-mh','--mh-wave','--fast-deep','--fast-prefix','--skip-blocks','42,43,46','--packed-weights','--packed-c32','--fp8-normalized','--fp8-ffn','--fp8-av','--fp8-deep','--fp8-middle','--half-c32','--crop-c32','--fused-qkv-norm','--fused-mh-ffn','--tiled-mh-ffn-large','--mapped-c32','--vit-blocked','--vit-contract-blocked','--vit-weight-mask','1','--vit-pack-input','--elide-identity-shift','--raw-chain','--pre-main8','--post-merge-fold','--fused-ffn-project','--split-ffn-fused','--split-mix-blocked','--split-project-blocked','--vit-qkv-blocked','--mh-project-crop','--mh-input-mapped','--prefix-fused','--direct-prefix-input','--grouped-mh-contract','--ffn-qkv','--ffn-qkv-max-c','256','--vit-qkv-fused','--vit-attn-fused','--vit-qkv-fp8','--vit-expand-frag','--split-mix-h16w','--pool-project-h16w','--decoder-h16w','--c512-qkv-frag','--c512-proj-frag','--c512-proj-tiles','--mh-proj-diag','--post-head-fused','--c32-finish-fused','--down-crop-fused','--pool32-h16w','--pool-project-group','--vit-proj-frag','--vit-qkv-frag','--vit-contract-frag','--prefix-inline')
$ref+=@('--seed','123','--history',"$r\input960.rgba32f",'--repeat','2')
& "$r\reference_g960.exe" @ref > "$r\g960-history.log"
if($LASTEXITCODE){Get-Content "$r\g960-history.log" | Select-Object -Last 5;throw 'history reference failed'}
Get-Content "$r\g960-history.log" | Select-String 'reference complete'

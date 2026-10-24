param([string]$Candidate='x',[string]$Modules='ffnh2-modules',[string]$Runner='benchmark_pinline.exe',[string]$FlagsBase='vitcf-on-flags.txt',[string]$Extra='',[string]$RefFlags='',[string]$Reference='reference_vitcf.exe')
# PSNR-gated twin of validate-modules.ps1: runs the same three checks but writes outputs instead of enforcing hashes.
# Outputs: $Candidate-p-full.f16 (40 frames), $Candidate-p-reset.f16 (24 frames, reset every 8), $Candidate-p-history.f32 (seed 123 + history).
# $Extra: env lines 'K=V;K=V' appended to the flag file; $RefFlags: extra CLI flags for the reference exe (e.g. '--foo').
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\$FlagsBase")
if($Extra){$keys=@($Extra.Split(';')|ForEach-Object{$_.Split('=')[0]});$base=@($base|Where-Object{$k=$_.Split('=')[0];$keys -notcontains $k})+@($Extra.Split(';'))}
$base|Set-Content "$r\$Candidate-p-flags.txt"
& "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name "$Candidate-p-full" -Flags "$Candidate-p-flags.txt"
& "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name "$Candidate-p-reset" -Flags "$Candidate-p-flags.txt" -Frames 24 -ResetEvery 8
$ref=@("$a","$r\$Modules","$r\input900.rgba32f","$a\noise.f32","$r\$Candidate-p-history.f32",'--900','--wmma','--wave','--tiled','--pooled','--fused-c32','--fused-ffn','--fused-mh','--fast-mh','--mh-wave','--fast-deep','--fast-prefix','--skip-blocks','42,43,46','--packed-weights','--packed-c32','--fp8-normalized','--fp8-ffn','--fp8-av','--fp8-deep','--fp8-middle','--half-c32','--crop-c32','--fused-qkv-norm','--fused-mh-ffn','--tiled-mh-ffn-large','--mapped-c32','--vit-blocked','--vit-contract-blocked','--vit-weight-mask','1','--vit-pack-input','--elide-identity-shift','--raw-chain','--pre-main8','--post-merge-fold','--fused-ffn-project','--split-ffn-fused','--split-mix-blocked','--split-project-blocked','--vit-qkv-blocked','--mh-project-crop','--mh-input-mapped','--prefix-fused','--direct-prefix-input','--grouped-mh-contract','--ffn-qkv','--ffn-qkv-max-c','256','--vit-qkv-fused','--vit-attn-fused','--vit-qkv-fp8','--vit-expand-frag','--split-mix-h16w','--pool-project-h16w','--decoder-h16w','--c512-qkv-frag','--c512-proj-frag','--c512-proj-tiles','--mh-proj-diag','--post-head-fused','--c32-finish-fused','--down-crop-fused','--pool32-h16w','--pool-project-group','--vit-proj-frag','--vit-qkv-frag','--vit-contract-frag','--prefix-inline')
if($RefFlags){$ref+=@($RefFlags.Split(' '))}
$ref+=@('--seed','123','--history',"$r\input900.rgba32f",'--repeat','2')
& "$r\$Reference" @ref > "$r\$Candidate-p-history.log"
if($LASTEXITCODE){throw 'history reference failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard timings'}
Write-Output ("outputs: $Candidate-p-full.f16 "+(Get-FileHash "$r\$Candidate-p-full.f16").Hash+" $Candidate-p-reset.f16 "+(Get-FileHash "$r\$Candidate-p-reset.f16").Hash+" $Candidate-p-history.f32 "+(Get-FileHash "$r\$Candidate-p-history.f32").Hash)

param([string]$Reference='reference_sparse.exe',[string]$Modules='ffnh2-modules')
# Bisects the sparse-weight hash mismatch by weight kind: the seed-123 history reference is run with --sparse-weights --sparse-filter <suffix> per kind.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
$Candidate='sparsefull'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$ref=@("$a","$r\$Modules","$r\input900.rgba32f","$a\noise.f32","$r\$Candidate-history.f32",'--900','--wmma','--wave','--tiled','--pooled','--fused-c32','--fused-ffn','--fused-mh','--fast-mh','--mh-wave','--fast-deep','--fast-prefix','--skip-blocks','42,43,46','--packed-weights','--packed-c32','--fp8-normalized','--fp8-ffn','--fp8-av','--fp8-deep','--fp8-middle','--half-c32','--crop-c32','--fused-qkv-norm','--fused-mh-ffn','--tiled-mh-ffn-large','--mapped-c32','--vit-blocked','--vit-contract-blocked','--vit-weight-mask','1','--vit-pack-input','--elide-identity-shift','--raw-chain','--pre-main8','--post-merge-fold','--fused-ffn-project','--split-ffn-fused','--split-mix-blocked','--split-project-blocked','--vit-qkv-blocked','--mh-project-crop','--mh-input-mapped','--prefix-fused','--direct-prefix-input','--grouped-mh-contract','--ffn-qkv','--ffn-qkv-max-c','256','--vit-qkv-fused','--vit-attn-fused','--vit-qkv-fp8','--vit-expand-frag','--split-mix-h16w','--pool-project-h16w','--decoder-h16w','--c512-qkv-frag','--c512-proj-frag','--c512-proj-tiles','--mh-proj-diag','--post-head-fused','--c32-finish-fused','--down-crop-fused','--pool32-h16w','--pool-project-group','--vit-proj-frag','--vit-qkv-frag','--vit-contract-frag','--prefix-inline')
$ref+=@('--seed','123','--history',"$r\input900.rgba32f",'--repeat','1','--sparse-weights')
foreach($k in @('')){
 & "$r\$Reference" @($ref+@('--sparse-full')) > "$r\sparsefull.log" 2>&1
 if($LASTEXITCODE){Write-Output ("{0,-34} FAILED rc={1}" -f $k,$LASTEXITCODE);continue}
 $h=(Get-FileHash "$r\$Candidate-history.f32").Hash
 Write-Output ("{0,-34} {1}" -f $k,$(if($h -eq '75B62D2F36B6861B1536EC06B087C3DDB8850F4CDF810E734E16E2BC0223C3F8'){'OK'}else{'MISMATCH'}))
}

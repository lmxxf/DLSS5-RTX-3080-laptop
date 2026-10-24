$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
$base|Set-Content "$r\dupvh-none-flags.txt"
$fam=[ordered]@{'expand'='vit_expand_blocked_fp8_frag_bytein$';'contract'='vit_contract_blocked_fp8$';'qkv'='vit_qkv_project_normalize_fused_f16compact_fp8$';'attn'='vit_attention_fused_400_bytein$';'project'='vit_project$';'gatherpack'='vit_gather'}
foreach($k in $fam.Keys){($base+@("DLSS5_HIP_DUP_PREFIX=$($fam[$k])",'DLSS5_HIP_DUP_COUNT=2'))|Set-Content "$r\dupvh-$k-flags.txt"}
$jobs=@('none')+@($fam.Keys)+@('none')
$i=0;foreach($k in $jobs){
 Write-Output "ROUND=$k"
 & "$r\validate-hdr.ps1" -Runner benchmark_pinline.exe -Modules poolg-modules -Name "dupvh-$i-$k" -Flags "dupvh-$k-flags.txt" -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 $i++
}

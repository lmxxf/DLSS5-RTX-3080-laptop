param([int]$Part=0,[string]$Runner="benchmark_vitcf.exe",[string]$Modules="vith-modules",[string]$FlagsBase="vitcf-on-flags.txt",[string]$Tag="dupm2")
# In-frame cost map of the current HIP build: each family's kernels launched twice (DLSS5_HIP_DUP_PREFIX, '$' = exact name), frame delta vs none.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\$FlagsBase"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
$base|Set-Content "$r\dupm-none-flags.txt"
$fam=[ordered]@{
 'c64ffn'='mh_ffn_fused_c64';'c64attn'='c64_attention_project';'c128ffn'='mh_ffn_fused_c128';'c128attn'='c128_attention_project';
 'c256ffn'='mh_ffn_fused_c256';'c256attn'='c256_attention_project';'c32pre'='c32_fast_ffn_attention_fused_half_finish_main8$';
 'c32mapped'='c32_fast_ffn_attention_fused_half_mapped$';'c32chain'='c32_fast_ffn_attention_fused_half_chain$';'c32finish'='c32_fast_ffn_attention_fused_half_chain_finish';
 'post'='c32_post_merge_head_half$';'vit'='vit_';'pool'='mh_pool';'decoder'='decoder_project2x';'prefix'='dlss5_prefix'
}
foreach($k in $fam.Keys){($base+@("DLSS5_HIP_DUP_PREFIX=$($fam[$k])",'DLSS5_HIP_DUP_COUNT=2'))|Set-Content "$r\dupm-$k-flags.txt"}
$keys=@($fam.Keys)
$jobs=if($Part -eq 0){@('none')+$keys[0..6]+@('none')}else{@('none')+$keys[7..14]+@('none')}
$i=0;foreach($k in $jobs){
 Write-Output "ROUND=$k"
 & "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name "$Tag-$Part-$i-$k" -Flags "dupm-$k-flags.txt" -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 $i++
}

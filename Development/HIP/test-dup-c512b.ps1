param([string]$Modules='ffnh2-modules',[string]$Runner='benchmark_pinline.exe',[string]$FlagsBase='vitcf-on-flags.txt',[string]$Tag='dupc512')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\$FlagsBase"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
$base|Set-Content "$r\$Tag-none-flags.txt"
$fam=[ordered]@{'c512split'='split_';'c512qkv'='mh_qkv_normalize_frag_c512$';'c512attn'='mh_attention_project_frag_c512$'}
foreach($k in $fam.Keys){($base+@("DLSS5_HIP_DUP_PREFIX=$($fam[$k])",'DLSS5_HIP_DUP_COUNT=2'))|Set-Content "$r\$Tag-$k-flags.txt"}
$i=0;foreach($k in @('none')+@($fam.Keys)+@('none')){
 Write-Output "ROUND=$k"
 & "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name "$Tag-$i-$k" -Flags "$Tag-$k-flags.txt" -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 $i++
}

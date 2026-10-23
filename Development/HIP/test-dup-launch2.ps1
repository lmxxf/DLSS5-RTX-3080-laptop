param([int]$Part=0)
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX='})
($base+@('DLSS5_HIP_DUP_PREFIX=mh_ffn_fused_c128'))|Set-Content "$r\dup-c128ffn-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=c128_attention_project'))|Set-Content "$r\dup-c128attn-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=c256_attention_project'))|Set-Content "$r\dup-c256attn-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=vit_'))|Set-Content "$r\dup-vit-flags.txt"
$jobs=if($Part -eq 0){@(@(0,'dup-none-flags.txt'),@(1,'dup-c128ffn-flags.txt'),@(2,'dup-c128attn-flags.txt'),@(3,'dup-c256attn-flags.txt'),@(4,'dup-vit-flags.txt'),@(5,'dup-none-flags.txt'))}else{@(@(6,'dup-c128ffn-flags.txt'),@(7,'dup-c128attn-flags.txt'),@(8,'dup-c256attn-flags.txt'),@(9,'dup-vit-flags.txt'),@(10,'dup-none-flags.txt'))}
foreach($job in $jobs){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_dup.exe -Modules opt-base-modules -Name "dup2-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

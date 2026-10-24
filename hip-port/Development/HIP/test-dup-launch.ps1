# In-frame marginal cost of the C64 kernels: launch each twice (identical output) and read the frame delta.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX='})
$base|Set-Content "$r\dup-none-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=mh_ffn_fused_c64'))|Set-Content "$r\dup-c64ffn-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=c64_attention_project'))|Set-Content "$r\dup-c64attn-flags.txt"
($base+@('DLSS5_HIP_DUP_PREFIX=mh_ffn_fused_c256'))|Set-Content "$r\dup-c256ffn-flags.txt"
foreach($job in @(@(0,'dup-none-flags.txt'),@(1,'dup-c64ffn-flags.txt'),@(2,'dup-c64attn-flags.txt'),@(3,'dup-c256ffn-flags.txt'),@(4,'dup-none-flags.txt'),@(5,'dup-c64ffn-flags.txt'),@(6,'dup-c64attn-flags.txt'),@(7,'dup-c256ffn-flags.txt'),@(8,'dup-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_dup.exe -Modules opt-base-modules -Name "dup-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

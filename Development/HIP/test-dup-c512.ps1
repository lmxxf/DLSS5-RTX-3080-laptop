param([int]$Part=0)
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT='})
$names=@('split_mix_blocked$','split_ffn_fused_fp8$','split_projection_blocked$','mh_qkv_normalize_fused$','mh_attention_fused_fp8_out$','mh_attention')
$i=0;foreach($n in $names){($base+@("DLSS5_HIP_DUP_PREFIX=$n"))|Set-Content "$r\dup512-$i-flags.txt";$i++}
$jobs=if($Part -eq 0){@(@('none','dup-none-flags.txt'),@('mix','dup512-0-flags.txt'),@('ffn','dup512-1-flags.txt'),@('proj','dup512-2-flags.txt'))}else{@(@('qkvn','dup512-3-flags.txt'),@('attn','dup512-4-flags.txt'),@('attnall','dup512-5-flags.txt'),@('none2','dup-none-flags.txt'))}
foreach($job in $jobs){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_dupp.exe -Modules opt-base-modules -Name "dup512-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

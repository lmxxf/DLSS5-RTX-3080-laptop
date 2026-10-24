$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT=|^DLSS5_SKIP_BLOCKS='})
($base+@('DLSS5_SKIP_BLOCKS=42,43,46'))|Set-Content "$r\dupc-none-flags.txt"
($base+@('DLSS5_SKIP_BLOCKS=42,43,46','DLSS5_HIP_DUP_PREFIX=mh_ffn_fused_c256','DLSS5_HIP_DUP_COUNT=2'))|Set-Content "$r\dupc-x2-flags.txt"
($base+@('DLSS5_SKIP_BLOCKS=42,43,46','DLSS5_HIP_DUP_PREFIX=mh_ffn_fused_c256','DLSS5_HIP_DUP_COUNT=3'))|Set-Content "$r\dupc-x3-flags.txt"
($base+@('DLSS5_SKIP_BLOCKS=15,16,17,18,19,20,21,22,48,49,50,51,52,53,54,55,42,43,46'))|Set-Content "$r\dupc-skip-flags.txt"
foreach($job in @(@(0,'dupc-none-flags.txt',1),@(1,'dupc-x2-flags.txt',1),@(2,'dupc-x3-flags.txt',1),@(3,'dupc-skip-flags.txt',0),@(4,'dupc-none-flags.txt',1))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 if($job[2]){& "$r\validate-hdr.ps1" -Runner benchmark_dupc.exe -Modules opt-base-modules -Name "dupc-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58}
 else{& "$r\validate-hdr.ps1" -Runner benchmark_dupc.exe -Modules opt-base-modules -Name "dupc-$($job[0])" -Flags $job[1] -EdgesOnly 1}
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

# Non-block stages: HLSL in-frame GPU stage profile (one round) + HIP dup by kernel prefix for prefix/post/pool/up/gather.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DUP_PREFIX=|^DLSS5_HIP_DUP_COUNT=|^DLSS5_NETWORK_GPU_PROFILE='})
($base+@('DLSS5_NETWORK_GPU_PROFILE=1'))|Set-Content "$r\hlsl-profile-flags.txt"
Write-Output "ROUND=hlsl-profile"
& "$r\validate-hdr.ps1" -Runner benchmark_hlsl_dup.exe -Modules opt-base-modules -Name "stage-hlsl-profile" -Flags hlsl-profile-flags.txt -EdgesOnly 1 -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
foreach($p in @('dlss5_prefix','c32_post_merge','mh_pool','decoder_project2x','vit_gather')){($base+@("DLSS5_HIP_DUP_PREFIX=$p"))|Set-Content "$r\dup-$p-flags.txt"}
foreach($job in @(@('none','dup-none-flags.txt'),@('prefix','dup-dlss5_prefix-flags.txt'),@('post','dup-c32_post_merge-flags.txt'),@('pool','dup-mh_pool-flags.txt'),@('up','dup-decoder_project2x-flags.txt'),@('gather','dup-vit_gather-flags.txt'),@('none2','dup-none-flags.txt'))){
 Write-Output "ROUND=$($job[0]) flags=$($job[1])"
 & "$r\validate-hdr.ps1" -Runner benchmark_dupc.exe -Modules opt-base-modules -Name "stage-$($job[0])" -Flags $job[1] -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

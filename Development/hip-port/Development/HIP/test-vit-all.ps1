$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-validation-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_ATTN_FUSED=|^DLSS5_HIP_VIT_QKV_FP8=|^DLSS5_HIP_VIT_EXPAND_M4=|^DLSS5_HIP_VIT_EXPAND_FRAG='})
($base+@('DLSS5_HIP_VIT_ATTN_FUSED=0','DLSS5_HIP_VIT_QKV_FP8=0','DLSS5_HIP_VIT_EXPAND_FRAG=0'))|Set-Content "$r\vit-all-off-flags.txt"
($base+@('DLSS5_HIP_VIT_ATTN_FUSED=1','DLSS5_HIP_VIT_QKV_FP8=1','DLSS5_HIP_VIT_EXPAND_FRAG=1'))|Set-Content "$r\vit-all-on-flags.txt"
foreach($i in 0..3){
 $on=$i -in @(1,2)
 $modules=if($on){'vit-expand-fm4-modules'}else{'ffn-qkv-round-byte-release-modules'}
 $flags=if($on){'vit-all-on-flags.txt'}else{'vit-all-off-flags.txt'}
 Write-Output "ROUND=$i modules=$modules flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_expand_frag.exe -Modules $modules -Name "vit-all-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

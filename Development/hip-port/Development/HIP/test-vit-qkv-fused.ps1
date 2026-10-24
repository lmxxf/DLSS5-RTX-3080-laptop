$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\vit-qkv-fused-modules"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffn-qkv-release-modules\*.hsaco" $m -Force
Copy-Item "$r\vit-qkv-fused.hsaco" "$m\deep_fast-packed.hsaco" -Force
foreach($i in 0..3){
 $enabled=if($i -in @(1,2)){1}else{0}
 $lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_(VIT_QKV_FUSED|FFN_QKV|PREFIX_FUSED|DIRECT_INPUT|GROUPED_CONTRACT)'})
 $lines+=@("DLSS5_HIP_VIT_QKV_FUSED=$enabled",'DLSS5_HIP_FFN_QKV=1','DLSS5_HIP_FFN_QKV_MAX_C=256','DLSS5_HIP_PREFIX_FUSED=1','DLSS5_HIP_DIRECT_INPUT=1','DLSS5_HIP_GROUPED_CONTRACT=1');$lines|Set-Content "$r\vit-qkv-fused-flags.txt"
 Write-Output "ROUND=$i fused=$enabled"
 & "$r\validate-hdr.ps1" -Runner benchmark_vit_qkv_fused.exe -Modules vit-qkv-fused-modules -Name "vit-qkv-fused-$i" -Flags vit-qkv-fused-flags.txt -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

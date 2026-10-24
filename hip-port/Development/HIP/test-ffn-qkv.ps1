param([ValidateSet(0,64,128,256)][int]$BaselineMax=0,[ValidateSet(64,128,256)][int]$CandidateMax=64)
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\ffn-qkv-modules";$tag="ffn-qkv-$BaselineMax-$CandidateMax"
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\mh-grouped-contract-release-modules\*.hsaco" $m -Force
Copy-Item "$r\ffn-qkv.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
foreach($i in 0..3){
 $max=if($i -in @(1,2)){$CandidateMax}else{$BaselineMax};$enabled=if($max){1}else{0};$limit=if($max){$max}else{64}
 $lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_FFN_QKV'})
 $lines+=@("DLSS5_HIP_FFN_QKV=$enabled","DLSS5_HIP_FFN_QKV_MAX_C=$limit",'DLSS5_HIP_PREFIX_FUSED=1','DLSS5_HIP_DIRECT_INPUT=1','DLSS5_HIP_GROUPED_CONTRACT=1');$lines|Set-Content "$r\$tag-flags.txt"
 Write-Output "ROUND=$i max_channels=$max"
 & "$r\validate-hdr.ps1" -Runner benchmark_ffn_qkv.exe -Modules ffn-qkv-modules -Name "$tag-$i" -Flags "$tag-flags.txt" -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

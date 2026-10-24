param([ValidateSet(0,1)][int]$EdgesOnly=1,[ValidateSet(40)][int]$Frames=40,[string]$Tag='backend-current')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_(PREFIX_FUSED|DIRECT_INPUT|GROUPED_CONTRACT|FFN_QKV|VIT_QKV_FUSED)'})
$lines+=@('DLSS5_HIP_PREFIX_FUSED=1','DLSS5_HIP_DIRECT_INPUT=1','DLSS5_HIP_GROUPED_CONTRACT=1','DLSS5_HIP_FFN_QKV=1','DLSS5_HIP_FFN_QKV_MAX_C=256','DLSS5_HIP_VIT_QKV_FUSED=1');$lines|Set-Content "$r\$Tag-flags.txt"
foreach($i in 0..3){
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
 $hlsl=$i -in @(0,3)
 $exe=if($hlsl){'benchmark_hlsl_edges.exe'}else{'benchmark_vit_qkv_compact.exe'}
 $expected=if($hlsl){'C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B'}else{'FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58'}
 & "$r\validate-hdr.ps1" -Runner $exe -Modules ffn-qkv-round-byte-release-modules -Name "$Tag-$i" -Flags "$Tag-flags.txt" -Frames $Frames -EdgesOnly $EdgesOnly -ExpectedHash $expected
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

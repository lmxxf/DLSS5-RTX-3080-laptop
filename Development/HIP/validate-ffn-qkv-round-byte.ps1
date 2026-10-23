$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$lines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_VIT_QKV_FUSED=|^DLSS5_HIP_FFN_QKV|^DLSS5_HIP_GROUPED_CONTRACT=|^DLSS5_HIP_PREFIX_FUSED=|^DLSS5_HIP_DIRECT_INPUT='})
$lines+=@('DLSS5_HIP_VIT_QKV_FUSED=1','DLSS5_HIP_FFN_QKV=1','DLSS5_HIP_FFN_QKV_MAX_C=256','DLSS5_HIP_GROUPED_CONTRACT=1','DLSS5_HIP_PREFIX_FUSED=1','DLSS5_HIP_DIRECT_INPUT=1');$lines|Set-Content "$r\vit-qkv-validation-flags.txt"
& "$r\validate-hdr.ps1" -Runner benchmark_vit_qkv_compact.exe -Modules ffn-qkv-round-byte-modules -Name ffn-qkv-round-byte-full -Flags vit-qkv-validation-flags.txt -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
& "$r\validate-hdr.ps1" -Runner benchmark_vit_qkv_compact.exe -Modules ffn-qkv-round-byte-modules -Name ffn-qkv-round-byte-reset -Flags vit-qkv-validation-flags.txt -Frames 24 -ResetEvery 8 -ExpectedHash 22C171FCE0AA2DF325D3CEB65A7A1C3FFEFB56821B65A0834680506E9D05AFC8
& "$r\validate-ffn-qkv-round-byte-history.ps1" | Select-String 'iteration=|reference complete'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}


& "$r\test_ffn_qkv.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\ffn-qkv-round-byte-modules"
if($LASTEXITCODE){throw "Fused intermediate mismatch"}

$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m='decoder-tail-stream-modules'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force "$r\$m"|Out-Null
Copy-Item "$r\decoder-tail-modules\*.hsaco" "$r\$m" -Force
Copy-Item "$r\mh-byte-stream-diag-modules\multihead_fused_attention.hsaco" "$r\$m\multihead_fused_attention.hsaco" -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1'
& "$r\validate-c32-register-ex.ps1" -Extended -Candidate $m -Baseline $m -Tag tailfix -CandidateFlags $flags -Runner benchmark_decoder_tail.exe
& "$r\validate-c32-register-ex.ps1" -OnlyHeight 720 -Candidate $m -Baseline $m -Tag tailfix720 -CandidateFlags $flags -Runner benchmark_decoder_tail.exe

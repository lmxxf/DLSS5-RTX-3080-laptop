$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m='decoder-byte-modules'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
& "$r\test_decoder_byte.exe" 'D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets' "$r\$m" byte
if($LASTEXITCODE){throw 'Decoder byte coverage failed'}
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1'
& "$r\validate-c32-register-ex.ps1" -Extended -Candidate $m -Baseline $m -Tag decoderbyte -CandidateFlags $flags -Runner benchmark_decoder_byte.exe
& "$r\validate-c32-register-ex.ps1" -OnlyHeight 720 -Candidate $m -Baseline $m -Tag decoderbyte720 -CandidateFlags $flags -Runner benchmark_decoder_byte.exe

$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0'
foreach($height in 1080,900){foreach($i in 0..3){
 $m=if($i -in 0,3){"$r\ffn-direct-word-modules"}else{'D:\DLSSNR-Lab\dual-arch-modules\gfx1201'}
 & "$r\profile-1080.ps1" -Frames 120 -Tag "directword-recheck-$height-$i" -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $m -Runner benchmark_dual.exe -TimingOnly
}}

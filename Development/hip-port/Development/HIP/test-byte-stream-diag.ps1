# Candidate requires the isolated host build from mh-byte-stream-diag.patch.
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-byte-stream-diag-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\mh-ex-production-modules\*.hsaco" $m -Force
& "$r\..\rtc_compile.exe" "$m\multihead_fused_attention.hsaco" "$r\mh-byte-stream-diag.hip" comgr
if($LASTEXITCODE){throw 'Compile failed'}
foreach($i in 0..3){
 $flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1'
 if($i -in @(1,2)){$flags+=';DLSS5_HIP_MH_BYTE_STREAM=1'}
 & "$r\profile-1080.ps1" -Families none -Frames 60 -Tag "streamdiag-$i" -ExtraFlag $flags -Modules $m -Runner benchmark_byte_diag.exe
}

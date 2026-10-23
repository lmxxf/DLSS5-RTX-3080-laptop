$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
$cases=[ordered]@{base_before='';mh='DLSS5_HIP_MH_BYTE_STREAM=1';vit='DLSS5_HIP_VIT_BYTE_STREAM=1';both='DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_VIT_BYTE_STREAM=1';base_after=''}
foreach($k in $cases.Keys){
 "CASE=$k"
 & "$r\profile-1080.ps1" -Families none -Frames 60 -Tag "bytes1080-$k" -ExtraFlag $cases[$k] -Modules "$r\mh-ex-production-modules"
}

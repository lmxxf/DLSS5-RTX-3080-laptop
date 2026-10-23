$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$cases=[ordered]@{abba_a1='';abba_b1='DLSS5_HIP_VIT_EXPAND_M4=1';abba_b2='DLSS5_HIP_VIT_EXPAND_M4=1';abba_a2='';small='DLSS5_HIP_TILED_FFN_SMALL=1';base_after=''}
foreach($k in $cases.Keys){
 "CASE=$k"
 & "$r\profile-1080.ps1" -Families none -Tag "tune-$k" -ExtraFlag $cases[$k]
}

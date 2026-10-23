$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1'}else{''}
 & "$r\profile-1080.ps1" -Families none -Frames 60 -Tag "featurebyte-$i" -ExtraFlag $flags -Modules "$r\mh-ex-production-modules"
}

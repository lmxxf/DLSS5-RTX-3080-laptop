$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
foreach($i in 0..3){
 $m=if($i -in @(1,2)){"$r\mh-normalize-rcp-modules"}else{"$r\c32-normrcp-production-modules"}
 & "$r\profile-1080.ps1" -Families none -Frames 80 -Tag "mhrcp-long-$i" -Modules $m
}
& "$r\perf-c32-register-ex-900.ps1" -Candidate mh-normalize-rcp-modules -Baseline c32-normrcp-production-modules -Tag mhrcp900

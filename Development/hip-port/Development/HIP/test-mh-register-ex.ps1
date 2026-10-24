# Apply mh-register-ex.patch to a temporary source copy; prepend HIP_ISA_HALF=1 and HIP_MH_RTZ_ISA=1.
param([int]$Frames=40,[string]$Tag='mhex')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\mh-register-ex-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-normrcp-production-modules\*.hsaco" $m -Force
& "$r\..\rtc_compile.exe" "$m\multihead_fused_attention.hsaco" "$r\mh-register-ex.hip" comgr
if($LASTEXITCODE){throw 'Compilation failed'}
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){$m}else{"$r\c32-normrcp-production-modules"}
 "ROUND=$i candidate=$($i -in @(1,2))"
 & "$r\profile-1080.ps1" -Families none -Tag "$Tag-$i" -Frames $Frames -Modules $modules
}

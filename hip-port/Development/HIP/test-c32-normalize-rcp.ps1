# Apply c32-normalize-rcp.patch to a temporary production source copy; prepend HIP_ISA_HALF=1 and HIP_PREPACKED_WEIGHTS=1.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\c32-normalize-rcp-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-regex-production-modules\*.hsaco" $m -Force
& "$r\..\rtc_compile.exe" "$m\c32_fused_ffn_attention-packed.hsaco" "$r\c32-normalize-rcp.hip" comgr
if($LASTEXITCODE){throw 'Compilation failed'}
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){$m}else{"$r\c32-regex-production-modules"}
 "ROUND=$i candidate=$($i -in @(1,2))"
 & "$r\profile-1080.ps1" -Families none -Tag "normrcp-$i" -Modules $modules
}

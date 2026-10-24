# Apply vit-normalize-rcp.patch to a temporary deep_fast.hip; prepend HIP_ISA_HALF=1, HIP_PREPACKED_WEIGHTS=1, HIP_BRANCHLESS_F=1.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\vit-normalize-rcp-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-normrcp-production-modules\*.hsaco" $m -Force
& "$r\..\rtc_compile.exe" "$m\deep_fast-packed.hsaco" "$r\vit-normalize-rcp.hip" comgr
if($LASTEXITCODE){throw 'Compilation failed'}
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){$m}else{"$r\c32-normrcp-production-modules"}
 "ROUND=$i candidate=$($i -in @(1,2))"
 & "$r\profile-1080.ps1" -Families none -Tag "vitrcp-$i" -Modules $modules
}

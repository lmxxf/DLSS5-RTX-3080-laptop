# Apply c32-pair-prob.patch to a temporary copy of hip/c32_fused_ffn_attention.hip; prepend HIP_ISA_HALF=1, HIP_PREPACKED_WEIGHTS=1, HIP_C32_PAIR_PROB=1 and upload as c32-pair-prob.hip.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$m="$r\c32-pair-prob-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item 'D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets\HIP\*.hsaco' $m -Force
& "$r\..\rtc_compile.exe" "$m\c32_fused_ffn_attention-packed.hsaco" "$r\c32-pair-prob.hip" comgr
if($LASTEXITCODE){throw 'Compilation failed'}
foreach($i in 0..3){
 $modules=if($i -in @(1,2)){$m}else{''}
 "ROUND=$i candidate=$($i -in @(1,2))"
 & "$r\profile-1080.ps1" -Families none -Tag "pairprob-$i" -Modules $modules
}

# Generate mhex64/128/256.hip by replacing only the corresponding c*_attention_project_body with the body in mh-register-ex.patch; keep the rest of the production file unchanged.
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$base="$r\c32-normrcp-production-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
foreach($c in 64,128,256){
 $m="$r\mhex$c-modules";New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$base\*.hsaco" $m -Force
 & "$r\..\rtc_compile.exe" "$m\multihead_fused_attention.hsaco" "$r\mhex$c.hip" comgr|Out-Null
 if($LASTEXITCODE){throw 'Compile failed'}
}
$i=0
foreach($c in 0,64,128,256,256,128,64,0){
 $m=if($c){"$r\mhex$c-modules"}else{$base}
 & "$r\profile-1080.ps1" -Families none -Tag "mhex-split-$i-c$c" -Modules $m -Frames 60
 $i++
}

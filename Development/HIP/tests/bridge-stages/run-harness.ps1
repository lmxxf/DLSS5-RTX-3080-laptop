$ErrorActionPreference='Stop';$d='D:\DLSSNR-Lab\hip-backend\bridge-stages'
if(Get-Process LOP-Win64-Shipping,SB-Win64-Shipping,OnimushaWotS,re9,Magpie -ErrorAction SilentlyContinue){throw 'Game running'}
& "$d\compile-codec-pair.exe" "$d\old-shaders\native_codec_decode.hlsl" "$d\old-decode.cso" "$d\new-shaders\native_codec_decode.hlsl" "$d\new-decode.cso"
if($LASTEXITCODE){throw 'Shader pair failed'}
& "$d\codec-harness.exe" "$d\old-decode.cso" "$d\new-decode.cso" 1002 decode > "$d\legacy-harness.log"
if($LASTEXITCODE){Get-Content "$d\legacy-harness.log";throw 'Legacy harness failed'}
Get-Content "$d\legacy-harness.log"

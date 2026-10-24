$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\decoder-byte-production-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\decoder-fast-path-modules\*.hsaco" $m -Force
foreach($name in 'deep_fast','deep_fast-packed'){
 & "$r\build-modules.ps1" -Only $name -SourceDir $r -OutputDir $m -Compiler "$r\..\rtc_compile.exe"
}
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
$extra=@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1','DLSS5_HIP_DECODER_BYTE=1');$refs=@('--mh-feature-byte','--mh-proj-diag-fb','--mh-byte-stream','--decoder-byte')
@(Get-Content "$r\vitcf-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900w')+$extra|Set-Content "$r\decoder-byte-flags.txt"
& "$r\validate-modules.ps1" -Candidate decoder-byte-golden -Modules decoder-byte-production-modules -Assets $a -Flags decoder-byte-flags.txt -Runner benchmark_decoder_byte_production.exe -Reference reference_decoder_byte.exe -ReferenceArgs $refs
& "$r\validate-modules-960.ps1" -Candidate decoder-byte-golden960 -Modules decoder-byte-production-modules -Assets $a -Runner benchmark_decoder_byte_production.exe -Reference reference_decoder_byte.exe -ExtraFlags $extra -ReferenceArgs $refs

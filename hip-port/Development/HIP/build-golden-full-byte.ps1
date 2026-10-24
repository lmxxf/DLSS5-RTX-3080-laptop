$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\full-byte-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\decoder-tail-modules\*.hsaco" $m -Force
& "$r\build-modules.ps1" -Only multihead_fused_attention -SourceDir $r -OutputDir $m -Compiler "$r\..\rtc_compile.exe"
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
$extra=@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1');$refs=@('--mh-feature-byte','--mh-proj-diag-fb','--mh-byte-stream')
@(Get-Content "$r\vitcf-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900w')+$extra|Set-Content "$r\full-byte-flags.txt"
& "$r\validate-modules.ps1" -Candidate full-byte-golden -Modules full-byte-modules -Assets $a -Flags full-byte-flags.txt -Runner benchmark_full_byte.exe -Reference reference_full_byte.exe -ReferenceArgs $refs
& "$r\validate-modules-960.ps1" -Candidate full-byte-golden960 -Modules full-byte-modules -Assets $a -Runner benchmark_full_byte.exe -Reference reference_full_byte.exe -ExtraFlags $extra -ReferenceArgs $refs

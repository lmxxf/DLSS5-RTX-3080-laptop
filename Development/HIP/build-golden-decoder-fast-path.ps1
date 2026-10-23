$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\decoder-fast-path-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\full-byte-modules\*.hsaco" $m -Force
foreach($name in 'deep_fast','deep_fast-packed'){
 & "$r\build-modules.ps1" -Only $name -SourceDir $r -OutputDir $m -Compiler "$r\..\rtc_compile.exe"
}
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
$extra=@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1');$refs=@('--mh-feature-byte','--mh-proj-diag-fb','--mh-byte-stream')
& "$r\validate-modules.ps1" -Candidate fast-path-golden -Modules decoder-fast-path-modules -Assets $a -Flags full-byte-flags.txt -Runner benchmark_full_byte.exe -Reference reference_full_byte.exe -ReferenceArgs $refs
& "$r\validate-modules-960.ps1" -Candidate fast-path-golden960 -Modules decoder-fast-path-modules -Assets $a -Runner benchmark_full_byte.exe -Reference reference_full_byte.exe -ExtraFlags $extra -ReferenceArgs $refs
& "$r\validate-c32-register-ex.ps1" -OnlyHeight 720 -Candidate decoder-fast-path-modules -Baseline full-byte-modules -Tag fastpath720 -CandidateFlags ($extra -join ';') -Runner benchmark_full_byte.exe

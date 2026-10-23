$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
$extra=@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1','DLSS5_HIP_DECODER_BYTE=1');$refs=@('--mh-feature-byte','--mh-proj-diag-fb','--mh-byte-stream','--decoder-byte')
@(Get-Content "$r\vitcf-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900w')+$extra|Set-Content "$r\dual-flags.txt"
# Root path exercises automatic selection; the reference CLI below uses the selected leaf.
& "$r\validate-hdr.ps1" -Assets $a -Runner benchmark_dual.exe -Modules '..\dual-arch-modules' -Name dual-auto -Flags dual-flags.txt -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
& "$r\validate-modules.ps1" -Candidate dual-golden -Modules '..\dual-arch-modules\gfx1201' -Assets $a -Flags dual-flags.txt -Runner benchmark_dual.exe -Reference reference_dual.exe -ReferenceArgs $refs
& "$r\validate-modules-960.ps1" -Candidate dual-golden960 -Modules '..\dual-arch-modules\gfx1201' -Assets $a -Runner benchmark_dual.exe -Reference reference_dual.exe -ExtraFlags $extra -ReferenceArgs $refs
Get-Content 'D:\DLSSNR-Lab\logs\native-hip-device.txt' -Tail 4

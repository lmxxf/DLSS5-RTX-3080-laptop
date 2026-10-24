$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
# 900w is aligned and must still match the established goldens.
& "$r\validate-modules.ps1" -Candidate tailfix-golden -Assets $a -Modules decoder-tail-modules -Runner benchmark_production.exe -Reference reference_production.exe
# Verify the corrected 960-row goldens. Original values included unwritten decoder48 outputs.
& "$r\validate-modules-960.ps1" -Candidate tailfix-golden960 -Assets $a -Modules decoder-tail-modules -Runner benchmark_production.exe -Reference reference_production.exe

$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
& "$r\test_mh_byte_diag.exe" 'D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets' "$r\mh-byte-stream-diag-modules" diag > "$r\profile1080\streamdiag-kernels.log"
$code=$LASTEXITCODE
Get-Content "$r\profile1080\streamdiag-kernels.log"|Select-String 'diff=|MISMATCH|matches'
if($code){throw 'Kernel equivalence failed'}

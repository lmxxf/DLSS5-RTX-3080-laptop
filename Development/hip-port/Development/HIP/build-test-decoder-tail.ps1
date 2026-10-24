$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\decoder-tail-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\mh-ex-production-modules\*.hsaco" $m -Force
foreach($name in 'deep_fast','deep_fast-packed','deep_wmma'){
 & "$r\build-modules.ps1" -Only $name -SourceDir $r -OutputDir $m -Compiler "$r\..\rtc_compile.exe"
}
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
$ErrorActionPreference='Continue'
& "$r\test_decoder_tail.exe" $a $m legacy > "$r\decoder-tail-legacy.log" 2>&1
$legacyCode=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($legacyCode -ne 1){throw 'Legacy launch did not reproduce failure'}
if(!(Select-String "$r\decoder-tail-legacy.log" -Pattern 'unwritten=3072' -Quiet)){throw 'Unexpected legacy failure'}
Get-Content "$r\decoder-tail-legacy.log"
& "$r\test_decoder_tail.exe" $a $m
if($LASTEXITCODE){throw 'Decoder tail tests failed'}

$ErrorActionPreference='Stop'
$g='C:\Program Files (x86)\Steam\steamapps\common\Lies of P\LiesofP\Binaries\Win64'
$assets="$g\DLSS5-AMD\native-game-tiled-assets"
$source='D:\DLSSNR-Lab\lop-codec-fix\native_codec_decode.hlsl'
$target="$assets\native_codec_decode.hlsl"
$backup='D:\DLSSNR-Lab\liesofp-before-r11-shader'
$old='977C2D52F098703B0BA742C6CF277F0496BB7EE7368067D506E6364E1E8C0DFF'
$new='98A790D928E61C3EAB905F43374DC9A1E560AFF22946CD17B166CD0CA3E6C5F8'
if((Get-FileHash $target).Hash -ne $old){throw 'Unexpected installed shader'}
if((Get-FileHash $source).Hash -ne $new){throw 'Candidate shader mismatch'}
if(Test-Path $backup){throw 'Backup exists'}
$dll=(Get-FileHash "$g\dlss5-amd.addon64").Hash
New-Item -ItemType Directory $backup|Out-Null
Copy-Item $target "$backup\native_codec_decode.hlsl"
if((Get-FileHash "$backup\native_codec_decode.hlsl").Hash -ne $old){throw 'Backup mismatch'}
Copy-Item $source $target -Force
if((Get-FileHash $target).Hash -ne $new){throw 'Installed shader mismatch'}
if((Get-FileHash "$g\dlss5-amd.addon64").Hash -ne $dll){throw 'DLL changed'}
'SHADER_UPDATED; recreate the upscaler/input format to reload; DLL unchanged'

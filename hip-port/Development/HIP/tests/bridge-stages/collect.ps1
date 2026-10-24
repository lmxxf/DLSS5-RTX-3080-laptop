$ErrorActionPreference='Stop';$d='D:\DLSSNR-Lab\hip-backend\bridge-stages';$out="$d\evidence"
New-Item -ItemType Directory -Force $out|Out-Null
foreach($name in 'bridge-900-g0.log','bridge-1080-g0.log','bridge-900-g1.log','codec-1080-0.log','codec-720-0.log','codec-720-1.log','shaders.log','legacy-harness.log'){
 [IO.File]::WriteAllText("$out\$name",(Get-Content "$d\$name" -Raw))
}
$files=@('test.exe','codec.exe','compile-shaders.exe','codec-harness.exe','old-decode.cso','new-decode.cso','new-shaders\native_codec_decode.hlsl','new-shaders\native_codec_encode.hlsl')
$hashes=$files|ForEach-Object{[pscustomobject]@{path=$_;sha=(Get-FileHash "$d\$_").Hash}}
[IO.File]::WriteAllText("$out\artifacts.json",(ConvertTo-Json -InputObject $hashes))
Compress-Archive -Force -Path "$out\*" -DestinationPath "$d\evidence.zip"

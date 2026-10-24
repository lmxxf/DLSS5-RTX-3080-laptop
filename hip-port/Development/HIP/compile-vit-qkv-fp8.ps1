$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-vit-qkv-fp8\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vit-qkv-fp8.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vit-qkv-fp8.hsaco" "$r\vit-qkv-fp8.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vit-qkv-fp8-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffn-qkv-round-byte-release-modules\*.hsaco" $m -Force
Copy-Item "$r\vit-qkv-fp8.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\vit-qkv-fp8.hsaco").Hash)

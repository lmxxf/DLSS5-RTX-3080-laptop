$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-vit-ffn\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vit-ffn.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vit-ffn.hsaco" "$r\vit-ffn.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vit-ffn-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-base-modules\*.hsaco" $m -Force
Copy-Item "$r\vit-ffn.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\vit-ffn.hsaco").Hash)

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-vit-expand-frag\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vit-expand-frag.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vit-expand-frag.hsaco" "$r\vit-expand-frag.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vit-expand-frag-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\vit-qkv-fp8-modules\*.hsaco" $m -Force
Copy-Item "$r\vit-expand-frag.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\vit-expand-frag.hsaco").Hash)

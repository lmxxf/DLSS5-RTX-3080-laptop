$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-c512-mix\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\c512-mix.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c512-mix.hsaco" "$r\c512-mix.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c512-mix-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-lane-release-modules\*.hsaco" $m -Force
Copy-Item "$r\c512-mix.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\c512-mix.hsaco").Hash)

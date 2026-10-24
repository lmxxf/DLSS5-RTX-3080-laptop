$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-c512-mixw\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\c512-mixw.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c512-mixw.hsaco" "$r\c512-mixw.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c512-mixw-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-lane-release-modules\*.hsaco" $m -Force
Copy-Item "$r\c512-mixw.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\c512-mixw.hsaco").Hash)

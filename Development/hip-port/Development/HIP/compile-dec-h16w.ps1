$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-dec-h16w\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\dec-h16w.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\dec-h16w.hsaco" "$r\dec-h16w.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\dec-h16w-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\pool-h16w-modules\*.hsaco" $m -Force
Copy-Item "$r\dec-h16w.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\dec-h16w.hsaco").Hash)

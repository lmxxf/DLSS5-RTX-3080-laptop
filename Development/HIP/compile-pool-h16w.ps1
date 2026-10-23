$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-pool-h16w\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\pool-h16w.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\pool-h16w.hsaco" "$r\pool-h16w.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\pool-h16w-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c512-mixw-modules\*.hsaco" $m -Force
Copy-Item "$r\pool-h16w.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\pool-h16w.hsaco").Hash)

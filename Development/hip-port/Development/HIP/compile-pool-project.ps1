$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-pool-project\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\pool-project.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\pool-project.hsaco" "$r\pool-project.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\pool-project-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-base-modules\*.hsaco" $m -Force
Copy-Item "$r\pool-project.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\pool-project.hsaco").Hash)
Select-String -Path "$r\pool-project.hsaco.s" -Pattern '^\s+\.(vgpr_count|group_segment_fixed_size|private_segment_fixed_size):' | ForEach-Object { $_.Line.Trim() } | Select-Object -Last 9

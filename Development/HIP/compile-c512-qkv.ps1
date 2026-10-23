$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-c512-qkv\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\c512-qkv.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c512-qkv.hsaco" "$r\c512-qkv.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c512-qkv-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-base-modules\*.hsaco" $m -Force
Copy-Item "$r\c512-qkv.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\c512-qkv.hsaco").Hash)
Select-String -Path "$r\c512-qkv.hsaco.s" -Pattern '^\s+\.(vgpr_count|group_segment_fixed_size|private_segment_fixed_size):' | ForEach-Object { $_.Line.Trim() } | Select-Object -Last 9

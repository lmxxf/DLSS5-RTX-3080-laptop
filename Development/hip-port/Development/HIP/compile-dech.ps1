param([string]$Base='c32h')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_DEC_HOIST_SCALE 1`n"+[IO.File]::ReadAllText("$r\src-rtz\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\dech.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\dech.hsaco" "$r\dech.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\dech-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\$Base-modules\*.hsaco" $m -Force
Copy-Item "$r\dech.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("dech module sha256 "+(Get-FileHash "$r\dech.hsaco").Hash+" base=$Base")
$t=Get-Content "$r\dech.hsaco.s";$i=[array]::IndexOf($t,($t|Where-Object{$_ -match '^\s+\.name:\s+decoder_project2x_h16w$'}|Select-Object -First 1));$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'

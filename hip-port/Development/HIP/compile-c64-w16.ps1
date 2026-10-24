$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-c64-w16\multihead_fused_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\c64-w16.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c64-w16.hsaco" "$r\c64-w16.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c64-w16-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\dec-h16w-modules\*.hsaco" $m -Force
Copy-Item "$r\c64-w16.hsaco" "$m\multihead_fused_attention.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\c64-w16.hsaco").Hash)
$t=Get-Content "$r\c64-w16.hsaco.s";$i=[array]::IndexOf($t,($t|Where-Object{$_ -match '^\s+\.name:\s+c64_attention_project_w16$'}|Select-Object -First 1));$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'

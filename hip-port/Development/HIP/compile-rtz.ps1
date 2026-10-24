$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_MH_RTZ_ISA 1`n"+[IO.File]::ReadAllText("$r\src-rtz\multihead_fused_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\rtz.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\rtz.hsaco" "$r\rtz.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\rtz-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\bfall-modules\*.hsaco" $m -Force
Copy-Item "$r\rtz.hsaco" "$m\multihead_fused_attention.hsaco" -Force
Write-Output ("rtz module sha256 "+(Get-FileHash "$r\rtz.hsaco").Hash)
$t=Get-Content "$r\rtz.hsaco.s";foreach($n in 'c64_attention_project_diag','c128_attention_project_diag','c256_attention_project_diag'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}

param([string]$Base='c512h')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_VIT_HOIST_SCALE 1`n"+[IO.File]::ReadAllText("$r\src-rtz\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vith.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vith.hsaco" "$r\vith.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vith-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\$Base-modules\*.hsaco" $m -Force
Copy-Item "$r\vith.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("vith module sha256 "+(Get-FileHash "$r\vith.hsaco").Hash+" base=$Base")
$t=Get-Content "$r\vith.hsaco.s";foreach($n in 'vit_project_frag','vit_qkv_project_normalize_fused_f16compact_fp8_frag'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'}

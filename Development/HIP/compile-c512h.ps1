$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C512_HOIST_RES 1`n"+[IO.File]::ReadAllText("$r\src-rtz\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\c512h.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c512h.hsaco" "$r\c512h.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c512h-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32h-modules\*.hsaco" $m -Force
Copy-Item "$r\c512h.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("c512h module sha256 "+(Get-FileHash "$r\c512h.hsaco").Hash)
$t=Get-Content "$r\c512h.hsaco.s";foreach($n in 'mh_attention_project_frag_c512'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'}

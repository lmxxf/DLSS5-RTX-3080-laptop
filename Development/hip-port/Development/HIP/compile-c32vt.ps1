$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$n='c32vt'
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C32_VT 1`n"+[IO.File]::ReadAllText("$r\src-rtz\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw "COMGR failed $n"}
$m="$r\$n-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffnh2-modules\*.hsaco" $m -Force
Copy-Item "$r\$n.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
$t=Get-Content "$r\$n.hsaco.s";$i=[array]::IndexOf($t,($t|Where-Object{$_ -match '^\s+\.name:\s+c32_fast_ffn_attention_fused_half_chain$'}|Select-Object -First 1));$vg=($t[($i-40)..($i+12)]|Select-String 'vgpr_count').Line.Trim();$sp=($t[($i-40)..($i+12)]|Select-String 'private_segment').Line.Trim()
Write-Output ("$n sha256 "+(Get-FileHash "$r\$n.hsaco").Hash+" chain: $vg $sp")

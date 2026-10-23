$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$n='ffnabl'
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_FFN_ABLATE_ACT 1`n"+[IO.File]::ReadAllText("$r\src-rtz\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw "COMGR failed $n"}
$m="$r\$n-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffnh2-modules\*.hsaco" $m -Force
Copy-Item "$r\$n.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("$n sha256 "+(Get-FileHash "$r\$n.hsaco").Hash)
$t=Get-Content "$r\$n.hsaco.s";foreach($k in 'mh_ffn_fused_c64_project_mapped_g128_qkv','mh_ffn_fused_c64_project_mapped_g128_qkv_bytein_fb','mh_ffn_fused_c256_tiled_project_mapped_g128_qkv_bytein_fb'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output $k;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_BRANCHLESS_Q8 1`n"+[IO.File]::ReadAllText("$r\src-rtz\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\rtzq8.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\rtzq8.hsaco" "$r\rtzq8.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\rtzq8-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\rtz-modules\*.hsaco" $m -Force
Copy-Item "$r\rtzq8.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("rtzq8 module sha256 "+(Get-FileHash "$r\rtzq8.hsaco").Hash)
$t=Get-Content "$r\rtzq8.hsaco.s";foreach($n in 'mh_ffn_fused_c64_project_mapped_g128_qkv','mh_ffn_fused_c128_project_mapped_g128_qkv','mh_ffn_fused_c256_tiled_project_mapped_g128_qkv'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C32_HOIST_PW 1`n"+[IO.File]::ReadAllText("$r\src-rtz\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\c32h.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c32h.hsaco" "$r\c32h.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c32h-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\rtzq8-modules\*.hsaco" $m -Force
Copy-Item "$r\c32h.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
Write-Output ("c32h module sha256 "+(Get-FileHash "$r\c32h.hsaco").Hash)
$t=Get-Content "$r\c32h.hsaco.s";foreach($n in 'c32_fast_ffn_attention_fused_half_chain','c32_fast_ffn_attention_fused_half_chain_finish_dcrop','c32_fast_ffn_attention_fused_half_finish_main8'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment'}

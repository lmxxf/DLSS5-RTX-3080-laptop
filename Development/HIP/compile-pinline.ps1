$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-pinline\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\pinline.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\pinline.hsaco" "$r\pinline.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\pinline-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\poolg-modules\*.hsaco" $m -Force
Copy-Item "$r\pinline.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\pinline.hsaco").Hash)
$t=Get-Content "$r\pinline.hsaco.s";foreach($n in 'c32_fast_ffn_attention_fused_half_finish_main8','c32_fast_ffn_attention_fused_half_prefix_finish_main8'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}

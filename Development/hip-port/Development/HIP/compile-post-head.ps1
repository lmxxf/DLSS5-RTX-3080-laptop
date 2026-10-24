$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-post-head\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\post-head.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\post-head.hsaco" "$r\post-head.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\post-head-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\mh-diag-modules\*.hsaco" $m -Force
Copy-Item "$r\post-head.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\post-head.hsaco").Hash)
$t=Get-Content "$r\post-head.hsaco.s";foreach($n in 'c32_post_merge_fused_half','c32_post_merge_head_half'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}

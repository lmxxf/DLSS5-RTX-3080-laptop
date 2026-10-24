$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C32_LOCAL_ATTN_SYNC 1`n#define HIP_C32_LOCAL_FFN_SYNC 1`n"+[IO.File]::ReadAllText("$r\src-c32-attn\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\c32-attn.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\c32-attn.hsaco" "$r\c32-attn.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\c32-attn-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\opt-base-modules\*.hsaco" $m -Force
Copy-Item "$r\c32-attn.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\c32-attn.hsaco").Hash)
$t=Get-Content "$r\c32-attn.hsaco.s";foreach($n in 'c32_fast_ffn_attention_fused_half_chain','c32_fast_ffn_attention_fused_half_mapped','c32_post_merge_fused_half'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$n+'$')}|Select-Object -First 1));Write-Output $n;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$base=[IO.File]::ReadAllText("$r\src-c32-bf\c32_fused_ffn_attention.hip")
foreach($v in @(@('c32-bf',"#define HIP_C32_BRANCHLESS_F 1`n"),@('c32-bfp',"#define HIP_C32_BRANCHLESS_F 1`n#define HIP_C32_STAGE_PREFETCH 1`n"))){
 $n=$v[0];$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+$v[1]+$base+"`n"
 [IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
 & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr
 if($LASTEXITCODE){throw "COMGR failed $n"}
 $m="$r\$n-modules";New-Item -ItemType Directory -Force $m|Out-Null
 Copy-Item "$r\vitcf-modules\*.hsaco" $m -Force
 Copy-Item "$r\$n.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
 Write-Output ("$n module sha256 "+(Get-FileHash "$r\$n.hsaco").Hash)
 $t=Get-Content "$r\$n.hsaco.s";foreach($k in 'c32_fast_ffn_attention_fused_half_finish_main8','c32_fast_ffn_attention_fused_half_mapped','c32_fast_ffn_attention_fused_half_chain','c32_fast_ffn_attention_fused_half_chain_finish_dcrop','c32_post_merge_head_half'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output $k;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}
}

$ErrorActionPreference='Stop'
# Re-test three old C32 nulls on the leaner kernel: rolled loops (occupancy), wave-local syncs, prepacked residual diagonals.
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$base=[IO.File]::ReadAllText("$r\src-rtz\c32_fused_ffn_attention.hip")
foreach($v in @(@('c32nu',"#define HIP_C32_NO_UNROLL 1`n"),@('c32ls',"#define HIP_C32_LOCAL_FFN_SYNC 1`n#define HIP_C32_LOCAL_ATTN_SYNC 1`n"),@('c32dg',"#define HIP_C32_DIAG_WEIGHTS 1`n"))){
 $n=$v[0];$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+$v[1]+$base+"`n"
 [IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
 & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
 if($LASTEXITCODE){throw "COMGR failed $n"}
 $m="$r\$n-modules";New-Item -ItemType Directory -Force $m|Out-Null
 Copy-Item "$r\c32h-modules\*.hsaco" $m -Force
 Copy-Item "$r\$n.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
 $t=Get-Content "$r\$n.hsaco.s";$i=[array]::IndexOf($t,($t|Where-Object{$_ -match '^\s+\.name:\s+c32_fast_ffn_attention_fused_half_chain$'}|Select-Object -First 1));$vg=($t[($i-40)..($i+12)]|Select-String 'vgpr_count').Line.Trim();$sp=($t[($i-40)..($i+12)]|Select-String 'private_segment').Line.Trim()
 Write-Output ("$n sha256 "+(Get-FileHash "$r\$n.hsaco").Hash+" chain: $vg $sp")
}

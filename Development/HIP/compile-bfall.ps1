$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$pre="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"
# c32 with the new source defaults (no extra defines): must reproduce c32-bfp.hsaco
$src=$pre+[IO.File]::ReadAllText("$r\src-bfall\c32_fused_ffn_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\bfall-c32.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\bfall-c32.hsaco" "$r\bfall-c32.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed c32'}
Write-Output ("bfall-c32 sha256 "+(Get-FileHash "$r\bfall-c32.hsaco").Hash+" (c32-bfp "+(Get-FileHash "$r\c32-bfp.hsaco").Hash+")")
$m="$r\bfall-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c32-bfp-modules\*.hsaco" $m -Force
Copy-Item "$r\bfall-c32.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
foreach($v in @(@('deep_fast.hip','deep_fast-packed.hsaco'),@('multihead_fast_padded.hip','multihead-fast-padded-wave-packed.hsaco'),@('multihead_fused_attention.hip','multihead_fused_attention.hsaco'))){
 $n='bfall-'+[IO.Path]::GetFileNameWithoutExtension($v[0])
 $src=$pre+"#define HIP_BRANCHLESS_F 1`n"+[IO.File]::ReadAllText("$r\src-bfall\"+$v[0])+"`n"
 [IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
 & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr
 if($LASTEXITCODE){throw "COMGR failed $n"}
 Copy-Item "$r\$n.hsaco" ("$m\"+$v[1]) -Force
 $t=Get-Content "$r\$n.hsaco.s"
 $spill=($t|Select-String '^\s+\.private_segment_fixed_size:\s+[1-9]').Count
 Write-Output ("$n sha256 "+(Get-FileHash "$r\$n.hsaco").Hash+" kernels_with_spill=$spill")
}

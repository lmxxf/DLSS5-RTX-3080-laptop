$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-tsmall\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\tsmall.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\tsmall.hsaco" "$r\tsmall.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\tsmall-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\b4tail-modules\*.hsaco" $m -Force
Copy-Item "$r\tsmall.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\tsmall.hsaco").Hash)
$t=Get-Content "$r\tsmall.hsaco.s"
foreach($k in 'mh_ffn_fused_c64_project_g128_qkv','mh_ffn_fused_c64_tiled_project_g128_qkv','mh_ffn_fused_c64_tiled_project_mapped_g128_qkv','mh_ffn_fused_c128_project_g128_qkv','mh_ffn_fused_c128_tiled_project_g128_qkv','mh_ffn_fused_c128_tiled_project_mapped_g128_qkv'){
 $i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output "== $k";$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'
}

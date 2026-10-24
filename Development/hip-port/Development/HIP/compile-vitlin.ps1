$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-vitlin\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vitlin.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vitlin.hsaco" "$r\vitlin.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vitlin-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\poolg-modules\*.hsaco" $m -Force
Copy-Item "$r\vitlin.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\vitlin.hsaco").Hash)
$t=Get-Content "$r\vitlin.hsaco.s"
foreach($k in 'vit_project','vit_project_frag','vit_qkv_project_normalize_fused_f16compact_fp8','vit_qkv_project_normalize_fused_f16compact_fp8_frag'){
 $i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output "== $k";$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'
}

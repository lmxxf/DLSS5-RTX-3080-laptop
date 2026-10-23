$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-mh-diag\multihead_fused_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\mh-diag.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\mh-diag.hsaco" "$r\mh-diag.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\mh-diag-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c512-ptile-modules\*.hsaco" $m -Force
Copy-Item "$r\mh-diag.hsaco" "$m\multihead_fused_attention.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\mh-diag.hsaco").Hash)
$t=Get-Content "$r\mh-diag.hsaco.s"
foreach($k in 'c64_attention_project','c64_attention_project_diag','c128_attention_project','c128_attention_project_diag','c256_attention_project','c256_attention_project_diag'){
 $i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output "== $k";$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'
}

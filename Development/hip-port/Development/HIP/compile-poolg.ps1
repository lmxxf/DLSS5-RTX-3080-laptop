$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-poolg\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\poolg.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\poolg.hsaco" "$r\poolg.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\poolg-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\b4tail-modules\*.hsaco" $m -Force
Copy-Item "$r\poolg.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\poolg.hsaco").Hash)
$t=Get-Content "$r\poolg.hsaco.s"
foreach($k in 'mh_pool_project_group_c64','mh_pool_project_group_c128','mh_pool_project_group_c256'){
 $i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output "== $k";$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'
}

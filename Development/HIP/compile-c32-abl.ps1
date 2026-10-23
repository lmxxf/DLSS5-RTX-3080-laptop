$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$base=[IO.File]::ReadAllText("$r\src-rtz\c32_fused_ffn_attention.hip")
foreach($k in 1,2,3){
 $n="c32abl$k";$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C32_ABLATE $k`n"+$base+"`n"
 [IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
 & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
 if($LASTEXITCODE){throw "COMGR failed $n"}
 $m="$r\$n-modules";New-Item -ItemType Directory -Force $m|Out-Null
 Copy-Item "$r\ffnh2-modules\*.hsaco" $m -Force
 Copy-Item "$r\$n.hsaco" "$m\c32_fused_ffn_attention-packed.hsaco" -Force
 Write-Output ("$n sha256 "+(Get-FileHash "$r\$n.hsaco").Hash)
}

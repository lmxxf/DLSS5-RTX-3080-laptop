$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
# Recompile the production ffnh2 recipe twice into scratch names and compare with the deployed module.
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_FFN_HOIST_RES 2`n"+[IO.File]::ReadAllText("$r\src-rtz\multihead_fast_padded.hip")+"`n"
foreach($n in 'det-a','det-b'){
  [IO.File]::WriteAllText("$r\$n.generated.hip",$src,$utf8)
  & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
  if($LASTEXITCODE){throw "COMGR failed $n"}
}
Write-Output ("production "+(Get-FileHash "$r\ffnh2-modules\multihead-fast-padded-wave-packed.hsaco").Hash)
Write-Output ("det-a      "+(Get-FileHash "$r\det-a.hsaco").Hash)
Write-Output ("det-b      "+(Get-FileHash "$r\det-b.hsaco").Hash)

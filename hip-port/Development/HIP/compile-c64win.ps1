param([string]$Name='c64win',[string[]]$Defines=@(),[int]$Modules=1)
# $Name-modules = ffnh2-modules + c64-window-fused.hsaco built from hip\multihead_fast_padded.hip + Development\HIP\c64_window_fused.hip
# (copied to hip-backend\c64_window_fused.hip) with the padded-packed module's defines (HIP_ISA_HALF, HIP_PREPACKED_WEIGHTS, HIP_FFN_HOIST_RES 2)
# plus -Defines ('HIP_WF_PHASE 1', ...). -Modules 0: compile and print register/LDS stats only.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_FFN_HOIST_RES 2`n"
foreach($d in $Defines){$src+="#define $d`n"}
$src+=[IO.File]::ReadAllText('D:\DLSSNR-Lab\hip\multihead_fast_padded.hip')+"`n"+[IO.File]::ReadAllText("$r\c64_window_fused.hip")+"`n"
[IO.File]::WriteAllText("$r\$Name.generated.hip",$src,$utf8)
& 'D:\DLSSNR-Lab\hip\rtc_compile.exe' "$r\$Name.hsaco" "$r\$Name.generated.hip" comgr | Out-Null
if($LASTEXITCODE){throw "COMGR failed $Name"}
if($Modules){$m="$r\$Name-modules";Remove-Item $m -Recurse -Force -ErrorAction SilentlyContinue;New-Item -ItemType Directory $m|Out-Null
 Copy-Item "$r\ffnh2-modules\*.hsaco" $m;Copy-Item "$r\$Name.hsaco" "$m\c64-window-fused.hsaco" -Force}
Write-Output ("$Name "+(Get-FileHash "$r\$Name.hsaco").Hash.Substring(0,12))
$t=Get-Content "$r\$Name.hsaco.s";foreach($k in 'c64_window_fused','c64_window_fused_mapped'){$i=[array]::IndexOf($t,($t|Where-Object{$_ -match ('^\s+\.name:\s+'+$k+'$')}|Select-Object -First 1));Write-Output $k;$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'}

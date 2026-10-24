param([ValidateSet('Smoke','Install','Update','Mode','Restore','Status')][string]$Action='Status',[ValidateSet(0,1,2)][int]$Mode=2,[switch]$GpuDebug,[ValidateSet(0,1)][int]$Async=1)
$ErrorActionPreference='Stop'
$lab='D:\DLSSNR-Lab\pre-upscale'
$g='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$b="$lab\before-pre-upscale"
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Close Stellar Blade and Magpie first.'}}
if($Action -eq 'Smoke'){Closed;foreach($arg in @('', '--async')){& "$lab\smoke.exe" $arg;if($LASTEXITCODE){throw "GPU smoke failed: $LASTEXITCODE"}};exit}
if($Action -eq 'Install'){
 Closed
 if(Test-Path $b){throw 'Backup already exists'}
 New-Item -ItemType Directory $b|Out-Null
 Copy-Item "$g\dlss5-amd.addon64" "$b\dlss5-amd.addon64"
 Copy-Item "$g\DLSS5-AMD\native-game-flags.txt" "$b\native-game-flags.txt"
 Copy-Item "$g\OptiScaler.ini" "$b\OptiScaler.ini"
 Get-FileHash "$b\dlss5-amd.addon64","$b\native-game-flags.txt","$b\OptiScaler.ini"|Select-Object Path,Hash|ConvertTo-Json|Set-Content "$b\manifest.json"
 Copy-Item "$lab\native-pre-upscale.addon64" "$g\dlss5-amd.addon64" -Force
 if((Get-FileHash "$lab\native-pre-upscale.addon64").Hash -ne (Get-FileHash "$g\dlss5-amd.addon64").Hash){throw 'Installed addon hash mismatch'}
 $ini=Get-Content "$g\OptiScaler.ini" -Raw
 $ini=[regex]::Replace($ini,'(?m)^Dx12Upscaler=.*$','Dx12Upscaler=fsr31')
 $ini=[regex]::Replace($ini,'(?m)^LogLevel=.*$','LogLevel=2')
 [IO.File]::WriteAllText("$g\OptiScaler.ini",$ini)
}
if($Action -eq 'Update'){
 Closed
 if(!(Test-Path "$b\manifest.json")){throw 'Original backup missing'}
 Copy-Item "$lab\native-pre-upscale.addon64" "$g\dlss5-amd.addon64" -Force
 if((Get-FileHash "$lab\native-pre-upscale.addon64").Hash -ne (Get-FileHash "$g\dlss5-amd.addon64").Hash){throw 'Installed addon hash mismatch'}
}
if($Action -eq 'Mode' -or $Action -eq 'Install' -or $Action -eq 'Update'){
 Closed
 $p="$g\DLSS5-AMD\native-game-flags.txt"
 $lines=@(Get-Content $p|Where-Object{$_ -notmatch '^DLSS5_PRE_UPSCALE(_DEBUG|_ASYNC)?='})+"DLSS5_PRE_UPSCALE=$Mode"+"DLSS5_PRE_UPSCALE_ASYNC=$Async"
 if($GpuDebug){$lines+='DLSS5_PRE_UPSCALE_DEBUG=1'}
 [IO.File]::WriteAllLines($p,$lines,(New-Object Text.UTF8Encoding($false)))
 "PRE_UPSCALE_MODE=$Mode"
}
if($Action -eq 'Restore'){
 Closed
 $m=Get-Content "$b\manifest.json" -Raw|ConvertFrom-Json
 foreach($f in $m){if((Get-FileHash $f.Path).Hash -ne $f.Hash){throw 'Backup modified'}}
 Copy-Item "$b\dlss5-amd.addon64" "$g\dlss5-amd.addon64" -Force
 Copy-Item "$b\native-game-flags.txt" "$g\DLSS5-AMD\native-game-flags.txt" -Force
 Copy-Item "$b\OptiScaler.ini" "$g\OptiScaler.ini" -Force
 'RESTORED_0.23'
}
if($Action -eq 'Status'){
 Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue|Select-Object Id,CPU
 foreach($n in 'native-pre-upscale.txt','native-pre-exception.txt','native-pre-debug.txt','native-game-oneshot.txt'){
  if(Test-Path "$g\DLSS5-AMD\logs\$n"){$n;Get-Content "$g\DLSS5-AMD\logs\$n" -Tail 12}
 }
 if(Test-Path "$g\OptiScaler.log"){Get-Content "$g\OptiScaler.log" -Tail 8}
 Select-String -Path "$g\DLSS5-AMD\logs\native-submission-order.txt" -Pattern 'ffx_temporal|hook_status'|Select-Object -Last 6|ForEach-Object{$_.Line}
 Select-String -Path "$g\DLSS5-AMD\native-game-flags.txt" -Pattern 'PRE_UPSCALE'|ForEach-Object{$_.Line}
 Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddMinutes(-10);Id=1000,1001} -ErrorAction SilentlyContinue|Select-Object -First 3|ForEach-Object{$_.Message}
}

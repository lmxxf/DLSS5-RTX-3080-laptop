param([ValidateSet('Install','Enable','Disable','Update','Restore','Launch','Close','CloseWindow','Shot','Status')][string]$Action='Status')
$ErrorActionPreference='Stop'
$g='C:\Program Files (x86)\Steam\steamapps\common\RESIDENT EVIL requiem BIOHAZARD requiem'
$lab='D:\DLSSNR-Lab\re9-opti'
$source='D:\給網友打包\OptiScaler-DLSS5-AMD-0.24'
$backup="$lab\before"
function Closed {if(Get-Process re9 -ErrorAction SilentlyContinue){throw 'Close Resident Evil Requiem before changing files.'}}
if($Action -eq 'CloseWindow'){Get-Process re9 -ErrorAction SilentlyContinue|ForEach-Object{$_.CloseMainWindow()}|Out-File "$lab\close-result.txt";exit}
if($Action -eq 'Close' -or $Action -eq 'Shot'){
 $t=Get-ScheduledTask -TaskName dlss5game
 $taskArgs=if($Action -eq 'Close'){'-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File D:\DLSSNR-Lab\re9-opti\optiscaler-re9.ps1 -Action CloseWindow'}else{'-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File D:\DLSSNR-Lab\capture_amd_desktop.ps1 -Output D:\DLSSNR-Lab\re9-opti\screen.png'}
 $name=if($Action -eq 'Close'){'dlss5re9close'}else{'dlss5re9shot'}
 $a=New-ScheduledTaskAction -Execute powershell.exe -Argument $taskArgs
 Register-ScheduledTask -TaskName $name -Action $a -Principal $t.Principal -Settings $t.Settings -Force|Out-Null
 Start-ScheduledTask $name
 exit
}
if($Action -eq 'Install'){
 Closed
 if(Test-Path $backup){throw 'Backup exists; inspect before reinstalling.'}
 foreach($line in Get-Content "$source\SHA256SUMS.txt"){
  if((Get-FileHash (Join-Path $source $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Source package hash mismatch'}
 }
 $ref=Get-Content "$lab\reframework-source.json" -Raw|ConvertFrom-Json
 if((Get-FileHash "$lab\dinput8.dll").Hash -ne $ref.dll_sha256){throw 'REFramework hash mismatch'}
 $install=@(Get-ChildItem $source|ForEach-Object{$_.Name})+@('dinput8.dll','dlss5-amd.addon64.off')
 $save=@($install+@('config.ini','ReShade.ini','ReShade.log','reframework','re2_fw_config.txt','re2_framework_log.txt')|Sort-Object -Unique|Where-Object{Test-Path "$g\$_"})
 New-Item -ItemType Directory $backup|Out-Null
 foreach($n in $save){Copy-Item "$g\$n" "$backup\$n" -Recurse}
 [pscustomobject]@{install=$install;saved=$save;reframework=$ref}|ConvertTo-Json -Depth 5|Set-Content "$backup\manifest.json"
 Copy-Item "$source\*" $g -Recurse -Force
 Copy-Item "$lab\dinput8.dll" "$g\dinput8.dll"
 Move-Item "$g\dlss5-amd.addon64" "$g\dlss5-amd.addon64.off"
 'INSTALLED: OptiScaler + REFramework + ReShade; DLSS5 add-on disabled for baseline.'
}
if($Action -eq 'Update'){
 Closed
 if(!(Test-Path "$lab\before-root-fix.addon64")){Copy-Item "$g\dlss5-amd.addon64" "$lab\before-root-fix.addon64"}
 Copy-Item "$lab\native-re9.addon64" "$g\dlss5-amd.addon64" -Force
 if(Test-Path "$g\_storage_\dlss5-amd.addon64"){Copy-Item "$lab\native-re9.addon64" "$g\_storage_\dlss5-amd.addon64" -Force}
 Get-FileHash "$g\dlss5-amd.addon64"|ForEach-Object{$_.Hash}
}
if($Action -eq 'Enable' -or $Action -eq 'Disable'){
 Closed
 if($Action -eq 'Enable'){Move-Item "$g\dlss5-amd.addon64.off" "$g\dlss5-amd.addon64" -Force}
 else{Move-Item "$g\dlss5-amd.addon64" "$g\dlss5-amd.addon64.off" -Force;if(Test-Path "$g\_storage_\dlss5-amd.addon64"){Move-Item "$g\_storage_\dlss5-amd.addon64" "$g\_storage_\dlss5-amd.addon64.off" -Force}}
}
if($Action -eq 'Restore'){
 Closed
 $m=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 foreach($n in $m.install){if(Test-Path "$g\$n"){Remove-Item "$g\$n" -Recurse -Force}}
 foreach($n in $m.saved){Copy-Item "$backup\$n" "$g\$n" -Recurse -Force}
 'RESTORED original files; generated log/config files retained unless backed up.'
}
if($Action -eq 'Launch'){
 $t=Get-ScheduledTask -TaskName dlss5game
 $a=New-ScheduledTaskAction -Execute 'C:\Program Files (x86)\Steam\steam.exe' -Argument '-applaunch 3764200'
 Register-ScheduledTask -TaskName dlss5re9 -Action $a -Principal $t.Principal -Settings $t.Settings -Force|Out-Null
 Start-ScheduledTask dlss5re9
 'LAUNCH_REQUESTED'
}
if($Action -eq 'Status'){
 Get-Process re9,CrashReport -ErrorAction SilentlyContinue|Select-Object Id,ProcessName,CPU
 Get-ChildItem "$g\*.addon64*","$g\dxgi.dll","$g\dinput8.dll" -ErrorAction SilentlyContinue|Select-Object Name,Length
 foreach($n in 'OptiScaler.log','ReShade.log','re2_framework_log.txt','reframework\log.txt','DLSS5-AMD\logs\native-pre-upscale.txt','DLSS5-AMD\logs\native-game-oneshot.txt','DLSS5-AMD\logs\native-submission-order.txt'){
  if(Test-Path "$g\$n"){Write-Output "LOG: $n";Get-Content "$g\$n" -Tail 16}
 }
}

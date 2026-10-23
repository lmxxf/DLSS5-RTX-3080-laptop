param(
 [ValidateSet('Deploy','Restore','Status')][string]$Action='Status',
 [string]$Stage='D:\DLSSNR-Lab\fit-input',
 [string]$Magpie='D:\Magpie-DLSS5\Magpie-Experimental-x64\Magpie-Experimental-x64'
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$config=Join-Path $env:LOCALAPPDATA 'Magpie\config\v4\config.json'
$assets=Join-Path $Magpie 'DLSS5-AMD\native-game-tiled-assets'
$flags=Join-Path $Magpie 'DLSS5-AMD\native-game-flags.txt'
$backup=Join-Path $Stage 'before-fit-input'
$utf8=New-Object System.Text.UTF8Encoding($false)
$shaderNames=@('native_codec_encode.hlsl','native_codec_decode.hlsl','native_temporal_coordinates.hlsl')
$files=@(@{Source='dlss5-amd.addon64';Target=(Join-Path $Magpie 'dlss5-amd.addon64')})
foreach($name in $shaderNames){$files+=@{Source=$name;Target=(Join-Path $assets $name)}}
if($Action -eq 'Status'){
 Get-Process *Magpie* | Format-Table Id,Path -AutoSize
 Get-FileHash (Join-Path $Magpie 'dlss5-amd.addon64')
 (Get-Content $config -Raw -Encoding UTF8 | ConvertFrom-Json).scalingModes |
  Where-Object name -eq 'DLSS5-AMD' | ConvertTo-Json -Depth 20
 exit 0
}
if(Get-Process *Magpie* -ErrorAction SilentlyContinue){throw 'Exit Magpie, including its tray process, before changing DLL or config.'}
if($Action -eq 'Restore'){
 if(!(Test-Path (Join-Path $backup 'complete'))){throw 'No complete backup'}
 foreach($file in $files){Copy-Item (Join-Path $backup $file.Source) $file.Target -Force}
 Copy-Item (Join-Path $backup 'native-game-flags.txt') $flags -Force
 Copy-Item (Join-Path $backup 'config.json') $config -Force
 'Restored pre-fit DLL, shaders, flags and Magpie config.'
 exit 0
}
# Validate all candidate hashes and configuration before modifying the installation.
foreach($line in Get-Content (Join-Path $Stage 'SHA256SUMS.txt')){
 if($line -notmatch '^([0-9a-fA-F]{64})  (.+)$'){throw 'Invalid candidate checksum line'}
 if((Get-FileHash (Join-Path $Stage $Matches[2])).Hash -ne $Matches[1]){throw "Candidate checksum failed: $($Matches[2])"}
}
$cfg=Get-Content $config -Raw -Encoding UTF8 | ConvertFrom-Json
$groups=@($cfg.scalingModes | Where-Object name -eq 'DLSS5-AMD')
if($groups.Count -ne 1){throw 'Expected one DLSS5-AMD effect group'}
$first=@($groups[0].effects | Where-Object name -eq 'FSR3\FSR3_SR')
$last=@($groups[0].effects | Where-Object name -eq 'FSR4\FSR4_SR')
if($first.Count -ne 1 -or $last.Count -ne 1){throw 'Expected FSR3 followed by FSR4'}
if($groups[0].effects[0].name -ne 'FSR3\FSR3_SR' -or $groups[0].effects[1].name -ne 'FSR4\FSR4_SR'){throw 'Unexpected effect order'}
$first[0] | Add-Member -NotePropertyName scalingType -NotePropertyValue 0 -Force
$first[0] | Add-Member -NotePropertyName scale -NotePropertyValue ([pscustomobject]@{x=1.0;y=1.0}) -Force
$last[0] | Add-Member -NotePropertyName scalingType -NotePropertyValue 1 -Force
$last[0] | Add-Member -NotePropertyName scale -NotePropertyValue ([pscustomobject]@{x=1.0;y=1.0}) -Force
$newConfig=$cfg | ConvertTo-Json -Depth 50
$null=$newConfig | ConvertFrom-Json
if(!(Test-Path (Join-Path $backup 'complete'))){
 New-Item -ItemType Directory -Path $backup -Force | Out-Null
 foreach($file in $files){Copy-Item $file.Target (Join-Path $backup $file.Source) -Force}
 Copy-Item $flags (Join-Path $backup 'native-game-flags.txt') -Force
 Copy-Item $config (Join-Path $backup 'config.json') -Force
 [IO.File]::WriteAllText((Join-Path $backup 'complete'),'1',$utf8)
}
foreach($file in $files){Copy-Item (Join-Path $Stage $file.Source) $file.Target -Force}
# Preserve local flags; only opt in to this change.
$newFlags=@(Get-Content $flags | Where-Object {$_ -notmatch '^DLSS5_FIT_INPUT='})+@('DLSS5_FIT_INPUT=1')
[IO.File]::WriteAllLines($flags,$newFlags,$utf8)
[IO.File]::WriteAllText($config,$newConfig,$utf8)
foreach($file in $files){
 if((Get-FileHash $file.Target).Hash -ne (Get-FileHash (Join-Path $Stage $file.Source)).Hash){throw "Installed hash mismatch: $($file.Target)"}
}
'Deployed: original-size FSR3 -> fitted DLSS5 -> screen-fit FSR4 -> existing FG.'
Get-FileHash (Join-Path $Magpie 'dlss5-amd.addon64')

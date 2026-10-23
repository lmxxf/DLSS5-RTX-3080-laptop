param([ValidateSet('Native','OptiScalerOnly','ReShadeOnly','AddonCandidate','Restore','Status')][string]$Action='Status',
 [string]$Candidate='D:\DLSSNR-Lab\pre-upscale\native-idle-tracking.addon64',
 [string]$ExpectedSha='395DABFE20261832FAC8A43188EB69661BAA52EB140C8A99655D8B7F4E4AC75D')
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$original='D:\DLSSNR-Lab\stellarblade-before-optiscaler'
$backup='D:\DLSSNR-Lab\pre-upscale\before-native-city-test'
function Closed {if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Exit Stellar Blade first.'}}
function RestoreFiles($records){
 Closed
 foreach($r in $records){if((Get-FileHash "$backup\files\$($r.name)").Hash -ne $r.sha256){throw 'Backup hash mismatch'}}
 foreach($r in $records){Copy-Item "$backup\files\$($r.name)" "$game\$($r.name)" -Force;if((Get-FileHash "$game\$($r.name)").Hash -ne $r.sha256){throw 'Restored hash mismatch'}}
}
if($Action -eq 'Native'){
 Closed
 if(Test-Path $backup){throw 'Native comparison backup already exists; inspect it first'}
 if(Test-Path "$game\d3d12.dll"){throw 'Unexpected local d3d12.dll; inspect loader before native comparison'}
 $old=Get-Content "$original\manifest.json" -Raw|ConvertFrom-Json
 if($old.saved -notcontains 'amd_fidelityfx_dx12.dll'){throw 'Original FSR not in pre-OptiScaler backup'}
 $originalHash=(Get-FileHash "$original\amd_fidelityfx_dx12.dll").Hash
 $names=@($old.install|Where-Object{$_ -match '\.(dll|addon64)$' -and (Test-Path "$game\$_")})
 if($names -notcontains 'dxgi.dll' -or $names -notcontains 'dlss5-amd.addon64'){throw 'Expected current plugin installation missing'}
 New-Item -ItemType Directory "$backup\files" -Force|Out-Null
 $records=@(foreach($name in $names){
  $hash=(Get-FileHash "$game\$name").Hash;Copy-Item "$game\$name" "$backup\files\$name"
  if((Get-FileHash "$backup\files\$name").Hash -ne $hash){throw 'Backup verification failed'}
  [pscustomobject]@{name=$name;sha256=$hash}
 })
 [pscustomobject]@{files=$records;originalFsrSha=$originalHash}|ConvertTo-Json -Depth 4|Set-Content "$backup\manifest.json"
 $settings=Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'
 $settingsHash=(Get-FileHash $settings).Hash
 Copy-Item $settings "$backup\GameUserSettings.ini.snapshot"
 Copy-Item "$game\OptiScaler.ini" "$backup\OptiScaler.ini.snapshot"
 Copy-Item "$game\DLSS5-AMD\native-game-flags.txt" "$backup\native-game-flags.txt.snapshot"
 try{
  Closed
  foreach($r in $records){Remove-Item -LiteralPath "$game\$($r.name)"}
  Copy-Item "$original\amd_fidelityfx_dx12.dll" "$game\amd_fidelityfx_dx12.dll"
  if((Get-FileHash "$game\amd_fidelityfx_dx12.dll").Hash -ne $originalHash){throw 'Original FSR verification failed'}
  foreach($r in $records){if($r.name -ne 'amd_fidelityfx_dx12.dll' -and (Test-Path "$game\$($r.name)")){throw 'Plugin binary still present'}}
  if((Get-FileHash $settings).Hash -ne $settingsHash){throw 'Game settings changed during preparation'}
  'native'|Set-Content "$backup\state.txt"
  "NATIVE_READY disabled_binaries=$($records.Count-1) original_fsr_sha=$originalHash settings_unchanged=1 backup=$backup"
 }catch{RestoreFiles $records;throw}
}elseif($Action -eq 'OptiScalerOnly'){
 Closed
 if((Get-Content "$backup\state.txt" -Raw).Trim() -ne 'native'){throw 'OptiScaler-only step requires the verified native state'}
 if(Test-Path "$game\d3d12.dll"){throw 'Unexpected local D3D12 proxy'}
 foreach($name in @('ReShade64.dll','dlss5-amd.addon64')){if(Test-Path "$game\$name"){throw 'Unexpected addon loader still present'}}
 $m=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 if((Get-FileHash "$original\amd_fidelityfx_dx12.dll").Hash -ne $m.originalFsrSha){throw 'Original FSR backup changed'}
 $records=@($m.files|Where-Object{$_.name -notin @('ReShade64.dll','dlss5-amd.addon64')})
 $iniPath="$game\OptiScaler.ini";$ini=Get-Content $iniPath -Raw
 if([regex]::Matches($ini,'(?m)^\s*LoadReshade\s*=').Count -ne 1){throw 'Expected one LoadReshade setting'}
 $snapshot="$backup\OptiScaler.before-only.ini"
 if(Test-Path $snapshot){throw 'OptiScaler-only settings backup already exists'}
 Copy-Item $iniPath $snapshot
 $settings=Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'
 $settingsHash=(Get-FileHash $settings).Hash
 try{
  RestoreFiles $records
  $ini=[regex]::Replace($ini,'(?m)^(\s*LoadReshade\s*=\s*)[^\r\n]*','${1}false')
  [IO.File]::WriteAllText($iniPath,$ini,(New-Object Text.UTF8Encoding($false)))
  if((Get-Content $iniPath -Raw) -notmatch '(?m)^\s*LoadReshade\s*=\s*false\s*$'){throw 'ReShade disable verification failed'}
  if((Get-FileHash $settings).Hash -ne $settingsHash){throw 'Game graphics settings changed'}
  'optiscaler-only'|Set-Content "$backup\state.txt"
  "OPTISCALER_ONLY_READY restored_binaries=$($records.Count) LoadReshade=false addon_absent=1 settings_unchanged=1"
 }catch{
  Closed
  foreach($r in $records){if(Test-Path "$game\$($r.name)"){Remove-Item -LiteralPath "$game\$($r.name)"}}
  Copy-Item "$original\amd_fidelityfx_dx12.dll" "$game\amd_fidelityfx_dx12.dll" -Force
  Copy-Item $snapshot $iniPath -Force
  throw
 }
}elseif($Action -eq 'ReShadeOnly'){
 Closed
 if((Get-Content "$backup\state.txt" -Raw).Trim() -ne 'optiscaler-only'){throw 'ReShade stage requires OptiScaler-only baseline'}
 if(Test-Path "$game\d3d12.dll"){throw 'Unexpected local D3D12 proxy'}
 if(@(Get-ChildItem $game -Recurse -File -Filter *.addon64).Count){throw 'Unexpected active addon; inspect before enabling ReShade'}
 if(Test-Path "$game\ReShade64.dll"){throw 'ReShade already present'}
 $m=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 $records=@($m.files|Where-Object{$_.name -eq 'ReShade64.dll'})
 if($records.Count -ne 1){throw 'ReShade backup missing'}
 $iniPath="$game\OptiScaler.ini";$ini=Get-Content $iniPath -Raw
 if([regex]::Matches($ini,'(?m)^\s*LoadReshade\s*=').Count -ne 1){throw 'Expected one LoadReshade setting'}
 $snapshot="$backup\OptiScaler.before-reshade.ini"
 if(Test-Path $snapshot){throw 'ReShade-stage settings backup already exists'}
 Copy-Item $iniPath $snapshot
 $settings=Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'
 $tracked=@($settings,"$game\ReShade.ini","$game\ReShadePreset.ini")
 $hashes=@{};foreach($path in $tracked){$hashes[$path]=(Get-FileHash $path).Hash}
 try{
  RestoreFiles $records
  $ini=[regex]::Replace($ini,'(?m)^(\s*LoadReshade\s*=\s*)[^\r\n]*','${1}true')
  [IO.File]::WriteAllText($iniPath,$ini,(New-Object Text.UTF8Encoding($false)))
  if((Get-Content $iniPath -Raw) -notmatch '(?m)^\s*LoadReshade\s*=\s*true\s*$'){throw 'ReShade enable verification failed'}
  foreach($path in $tracked){if((Get-FileHash $path).Hash -ne $hashes[$path]){throw 'Game settings or ReShade preset changed'}}
  'reshade-no-addon'|Set-Content "$backup\state.txt"
  'RESHADE_ONLY_READY LoadReshade=true addon_absent=1 game_settings_and_preset_unchanged=1'
 }catch{
  Closed
  if(Test-Path "$game\ReShade64.dll"){Remove-Item -LiteralPath "$game\ReShade64.dll"}
  Copy-Item $snapshot $iniPath -Force
  throw
 }
 }elseif($Action -eq 'AddonCandidate'){
 Closed
 if((Get-Content "$backup\state.txt" -Raw).Trim() -ne 'reshade-no-addon'){throw 'Candidate requires ReShade without addon baseline'}
 if(@(Get-ChildItem $game -Recurse -File -Filter *.addon64).Count){throw 'Unexpected active addon'}
 if((Get-FileHash $Candidate).Hash -ne $ExpectedSha){throw 'Candidate hash mismatch'}
 $m=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 foreach($r in $m.files){if($r.name -ne 'dlss5-amd.addon64' -and (Get-FileHash "$game\$($r.name)").Hash -ne $r.sha256){throw 'Baseline binary changed'}}
 $settings=Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'
 $tracked=@($settings,"$game\OptiScaler.ini","$game\ReShade.ini","$game\ReShadePreset.ini","$game\DLSS5-AMD\native-game-flags.txt")
 $hashes=@{};foreach($path in $tracked){$hashes[$path]=(Get-FileHash $path).Hash}
 try{
  Closed
  Copy-Item $Candidate "$game\dlss5-amd.addon64"
  if((Get-FileHash "$game\dlss5-amd.addon64").Hash -ne $ExpectedSha){throw 'Installed addon hash mismatch'}
  foreach($path in $tracked){if((Get-FileHash $path).Hash -ne $hashes[$path]){throw 'Configuration changed during deployment'}}
  'addon-idle-tracking-candidate'|Set-Content "$backup\state.txt"
  "ADDON_CANDIDATE_READY SHA=$ExpectedSha baseline_binaries_and_settings_unchanged=1"
 }catch{
  Closed
  if(Test-Path "$game\dlss5-amd.addon64"){Remove-Item -LiteralPath "$game\dlss5-amd.addon64"}
  'reshade-no-addon'|Set-Content "$backup\state.txt"
  throw
 }
}elseif($Action -eq 'Restore'){
 $m=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 RestoreFiles @($m.files)
 if(Test-Path "$backup\OptiScaler.before-only.ini"){Copy-Item "$backup\OptiScaler.before-only.ini" "$game\OptiScaler.ini" -Force}
 'restored'|Set-Content "$backup\state.txt"
 'PLUGIN_CHAIN_RESTORED; current game graphics settings preserved'
}else{
 Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue|Select-Object Id,ProcessName
 if(Test-Path "$backup\state.txt"){Get-Content "$backup\state.txt"}
 foreach($n in @('dxgi.dll','d3d12.dll','ReShade64.dll','dlss5-amd.addon64','amd_fidelityfx_dx12.dll')){
  if(Test-Path "$game\$n"){Get-FileHash "$game\$n"|Select-Object Path,Hash}
 }
}

param([ValidateSet('Install','Restore')][string]$Action='Install')
$ErrorActionPreference='Stop'
$g='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$r='D:\DLSSNR-Lab';$backup="$r\pre-upscale\before-decoder-tail"
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}}
function Restore {
 Closed;$records=@(Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json)
 foreach($v in $records){if((Get-FileHash (Join-Path "$backup\files" $v.relative)).Hash -ne $v.sha256){throw 'Backup checksum mismatch'}}
 foreach($v in $records){$dst=Join-Path $g $v.relative;Copy-Item (Join-Path "$backup\files" $v.relative) $dst -Force;if((Get-FileHash $dst).Hash -ne $v.sha256){throw 'Restore checksum mismatch'}}
 'RESTORED_DECODER_BASELINE'
}
Closed
if($Action -eq 'Restore'){Restore;exit}
if(Test-Path $backup){throw 'Backup already exists'}
$items=@(@{relative='dlss5-amd.addon64';source="$r\pre-upscale\native-decoder-tail.addon64";sha='174C78270B4A3AB7FD4E98B8933C87682F176688E25257760F3B370084C91D64'})
$hashes=@{'deep_fast.hsaco'='A77C349B55492464AA73FF7F946AE02D11C55A3737D18AA61774CE815ECB49D7';'deep_fast-packed.hsaco'='104E2C840C05F23794C47314DD41E7862031C0C98F7BDD6E13B40293DEEC2002';'deep_wmma.hsaco'='B562C8986300B0517818AE54A46108E725E1ECC6C6B6C88A3B7FA14C749A5B2F'}
foreach($name in $hashes.Keys){$items+=@{relative="DLSS5-AMD\native-game-tiled-assets\HIP\$name";source="$r\hip-backend\decoder-tail-modules\$name";sha=$hashes[$name]}}
if(Test-Path "$g\_storage_"){foreach($f in Get-ChildItem "$g\_storage_" -Recurse -File -Filter dlss5-amd.addon64){$items+=@{relative=$f.FullName.Substring($g.Length+1);source=$items[0].source;sha=$items[0].sha}}}
foreach($v in $items){if((Get-FileHash $v.source).Hash -ne $v.sha){throw 'Candidate checksum mismatch'};if(!(Test-Path (Join-Path $g $v.relative))){throw 'Installed file missing'}}
$watch=@("$g\DLSS5-AMD\native-game-flags.txt","$g\OptiScaler.ini",(Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'));$before=@{};foreach($f in $watch){$before[$f]=(Get-FileHash $f).Hash}
$records=@(foreach($v in $items){$src=Join-Path $g $v.relative;$dst=Join-Path "$backup\files" $v.relative;New-Item -ItemType Directory -Force (Split-Path $dst)|Out-Null;Copy-Item $src $dst;$hash=(Get-FileHash $src).Hash;if((Get-FileHash $dst).Hash -ne $hash){throw 'Backup copy mismatch'};[pscustomobject]@{relative=$v.relative;sha256=$hash}})
$records|ConvertTo-Json -Depth 3|Set-Content "$backup\manifest.json"
try{
 Closed
 foreach($v in $items){$dst=Join-Path $g $v.relative;Copy-Item $v.source $dst -Force;if((Get-FileHash $dst).Hash -ne $v.sha){throw 'Installed checksum mismatch'}}
 foreach($f in $watch){if((Get-FileHash $f).Hash -ne $before[$f]){throw 'Settings changed'}}
 "INSTALLED files=$($items.Count) settings_unchanged=1 backup=$backup"
 Get-Content $watch[0]|Select-String 'SHOW_FPS|NETWORK_HEIGHT|MH_FEATURE_BYTE|MH_PROJ_DIAG_FB|MH_BYTE_STREAM|VIT_BYTE_STREAM'
}catch{Restore;throw}

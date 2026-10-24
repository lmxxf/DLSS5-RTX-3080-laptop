param([ValidateSet('Install','Restore')][string]$Action='Install')
$ErrorActionPreference='Stop'
$g='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$addon='D:\DLSSNR-Lab\c256-frag-src\native-c256-fragment.addon64'
$modules='D:\DLSSNR-Lab\c256-frag-production-modules'
$manifest='D:\DLSSNR-Lab\pre-upscale\c256-fragment-SHA256SUMS'
$b='D:\DLSSNR-Lab\pre-upscale\before-c256-fragment'
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}}
function Restore {
 Closed
 foreach($r in Get-Content "$b\items.json" -Raw|ConvertFrom-Json){$dst=Join-Path $g $r;if(Test-Path $dst){Remove-Item $dst -Recurse -Force};Copy-Item (Join-Path "$b\files" $r) $dst -Recurse -Force}
 'RESTORED'
}
Closed
if($Action -eq 'Restore'){Restore;exit}
if(Test-Path $b){throw 'Backup exists'}
$hip='DLSS5-AMD\native-game-tiled-assets\HIP'
$flags='DLSS5-AMD\native-game-flags.txt'
$items=@('dlss5-amd.addon64',$hip,$flags)
if(Test-Path "$g\_storage_"){foreach($f in Get-ChildItem "$g\_storage_" -Recurse -File -Filter dlss5-amd.addon64){$items+=$f.FullName.Substring($g.Length+1)}}
if((Get-FileHash $addon).Hash -ne 'f5d3f7348e42f362a0db4233814e1b2d8c4842de0d1196620a40bbc299adde75'){throw 'Addon mismatch'}
foreach($a in 'gfx1200','gfx1201'){if(@(Get-ChildItem "$modules\$a\*.hsaco").Count -ne 24){throw 'Modules missing'}}
$sums=@(Get-Content $manifest)
if($sums.Count -ne 48){throw 'Expected 48 manifest entries'}
foreach($line in $sums){if((Get-FileHash (Join-Path $modules $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Source module checksum mismatch'}}
foreach($r in $items){$src=Join-Path $g $r;$dst=Join-Path "$b\files" $r;New-Item -ItemType Directory -Force (Split-Path $dst)|Out-Null;Copy-Item $src $dst -Recurse;foreach($f in Get-ChildItem $src -Recurse -File){$rel=$f.FullName.Substring($g.Length+1);if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash (Join-Path "$b\files" $rel)).Hash){throw 'Backup mismatch'}}}
ConvertTo-Json -InputObject $items|Set-Content "$b\items.json"
$ini=(Get-FileHash "$g\OptiScaler.ini").Hash
try {
 Closed
 foreach($r in $items|Where-Object{$_ -like '*.addon64'}){Copy-Item $addon (Join-Path $g $r) -Force;if((Get-FileHash (Join-Path $g $r)).Hash -ne (Get-FileHash $addon).Hash){throw 'Addon copy mismatch'}}
 Remove-Item "$g\$hip" -Recurse -Force
 foreach($arch in 'gfx1200','gfx1201'){
  New-Item -ItemType Directory -Force "$g\$hip\$arch"|Out-Null
  Copy-Item "$modules\$arch\*.hsaco" "$g\$hip\$arch"
 }
 foreach($line in $sums){if((Get-FileHash (Join-Path "$g\$hip" $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Installed module checksum mismatch'}}
 $v=Get-Content "$g\$flags" -Raw
 $settings=@{DLSS5_PRE_UPSCALE='1';DLSS5_PRE_UPSCALE_ASYNC='1';DLSS5_HIP_MH_FEATURE_BYTE='1';DLSS5_HIP_MH_PROJ_DIAG_FB='1';DLSS5_HIP_MH_BYTE_STREAM='1';DLSS5_HIP_DECODER_BYTE='1';DLSS5_HIP_MH_FFN_FRAG256='1';DLSS5_HIP_VIT_BYTE_STREAM='0'}
 foreach($k in $settings.Keys){$v=[regex]::Replace($v,"(?m)^$k=.*\r?\n?",'');$v=$v.TrimEnd()+"`r`n$k=$($settings[$k])`r`n"}
 $v=[regex]::Replace($v,'(?m)^DLSS5_HIP_MODULE_DIR=.*\r?\n?','')
 [IO.File]::WriteAllText("$g\$flags",$v)
 if((Get-FileHash "$g\OptiScaler.ini").Hash -ne $ini){throw 'OptiScaler settings changed'}
 'INSTALLED C256 fragment + direct input; 48 modules verified; backup='+$b
 Get-Content "$g\$flags"|Select-String 'NETWORK_HEIGHT|SHOW_FPS|NOTICE|HIP_MH_|DECODER_BYTE|VIT_BYTE_STREAM'
}catch{Restore;throw}

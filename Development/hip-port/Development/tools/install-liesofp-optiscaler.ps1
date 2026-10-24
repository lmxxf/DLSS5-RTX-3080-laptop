param([ValidateSet('Install','Restore')][string]$Action='Install')
$ErrorActionPreference='Stop'
$g='C:\Program Files (x86)\Steam\steamapps\common\Lies of P\LiesofP\Binaries\Win64'
$s='D:\給網友打包\OptiScaler-DLSS5-AMD-0.25'
$b='D:\DLSSNR-Lab\liesofp-before-optiscaler-025'
function Closed {if(Get-Process LOP,LOP-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit Lies of P/Magpie first'}}
function Restore {
 Closed
 $m=Get-Content "$b\manifest.json" -Raw|ConvertFrom-Json
 foreach($n in $m.installed){if(Test-Path "$g\$n"){Remove-Item "$g\$n" -Recurse -Force}}
 foreach($n in $m.saved){Copy-Item "$b\files\$n" "$g\$n" -Recurse -Force}
 'RESTORED Lies of P'
}
Closed
if($Action -eq 'Restore'){Restore;exit}
if(!(Test-Path "$g\LOP-Win64-Shipping.exe")){throw 'Game executable absent'}
if(Test-Path $b){throw 'Backup exists'}
$lines=@(Get-Content "$s\SHA256SUMS.txt")
foreach($line in $lines){if((Get-FileHash (Join-Path $s $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Release checksum mismatch'}}
$root=@('dxgi.dll','ReShade64.dll','dlss5-amd.addon64','OptiScaler.ini','DLSS5-AMD','D3D12_Optiscaler')
$installed=@($root+'OptiScaler')
# Also disable any pre-existing proxy/add-ons after backing them up.
$conflicts=@('d3d12.dll','winmm.dll','version.dll','ReShade.ini')+@(Get-ChildItem "$g\*.addon64" -ErrorAction SilentlyContinue|ForEach-Object Name)
$saved=@($installed+$conflicts|Sort-Object -Unique|Where-Object{Test-Path "$g\$_"})
New-Item -ItemType Directory -Force "$b\files"|Out-Null
$originalSdk=(Get-FileHash "$g\amd_fidelityfx_dx12.dll").Hash
foreach($n in $saved){Copy-Item "$g\$n" "$b\files\$n" -Recurse}
[pscustomobject]@{installed=@($installed+$conflicts|Sort-Object -Unique);saved=$saved;original_sdk_sha256=$originalSdk}|ConvertTo-Json -Depth 4|Set-Content "$b\manifest.json"
try {
 Closed
 foreach($n in @($installed+$conflicts|Sort-Object -Unique)){if(Test-Path "$g\$n"){Remove-Item "$g\$n" -Recurse -Force}}
 New-Item -ItemType Directory -Force "$g\OptiScaler"|Out-Null
 foreach($f in Get-ChildItem $s){$dst=if($f.Name -in $root){"$g\$($f.Name)"}else{"$g\OptiScaler\$($f.Name)"};Copy-Item $f.FullName $dst -Recurse}
 foreach($line in $lines){$rel=$line.Substring(66).Replace('/','\');$top=$rel.Split('\')[0];$dst=if($top -in $root){Join-Path $g $rel}else{Join-Path "$g\OptiScaler" $rel};if((Get-FileHash $dst).Hash -ne $line.Substring(0,64)){throw "Installed checksum mismatch: $rel"}}
 $ini=Get-Content "$g\OptiScaler.ini" -Raw
 $ini=[regex]::Replace($ini,'(?m)^OptiDllPath=.*$',"OptiDllPath=$g\OptiScaler")
 $ini=[regex]::Replace($ini,'(?m)^FfxDx12Path=.*$',"FfxDx12Path=$g\OptiScaler\amd_fidelityfx_dx12.dll")
 [IO.File]::WriteAllText("$g\OptiScaler.ini",$ini)
 $flags=Get-Content "$g\DLSS5-AMD\native-game-flags.txt" -Raw
 $flags=[regex]::Replace($flags,'(?m)^DLSS5_SHOW_FPS=.*$','DLSS5_SHOW_FPS=0')
 [IO.File]::WriteAllText("$g\DLSS5-AMD\native-game-flags.txt",$flags)
 if((Get-FileHash "$g\amd_fidelityfx_dx12.dll").Hash -ne $originalSdk){throw 'Original game SDK changed'}
 "INSTALLED OptiScaler 0.25 files_verified=$($lines.Count) original_sdk_preserved=1"
 Get-FileHash "$g\dxgi.dll","$g\dlss5-amd.addon64"
 "BACKUP $b"
}catch{Restore;throw}

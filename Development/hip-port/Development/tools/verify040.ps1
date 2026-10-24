# verify040.ps1 (0.40 packaging): file lists vs 0.39, payload hashes, RE9 replay smoke from a clean unzip, unzip-over-0.39 upgrade test.
$ErrorActionPreference='Stop';Add-Type -AssemblyName System.IO.Compression.FileSystem
$out='D:\給網友打包';$v='D:\DLSSNR-Lab\release-040\verify';Remove-Item -Recurse -Force $v -EA 0;New-Item -ItemType Directory $v|Out-Null
$pk=@('Magpie-DLSS5-AMD','OptiScaler-DLSS5-AMD','OptiScaler-REFramework-DLSS5-AMD')
function Entries($zip){$z=[IO.Compression.ZipFile]::OpenRead($zip);try{@($z.Entries|%{$_.FullName.Replace('\','/')})}finally{$z.Dispose()}}
foreach($p in $pk){$a=Entries "$out\$p-0.39.zip";$b=Entries "$out\$p-0.40.zip"
 "== $p : 0.39 $($a.Count) entries, 0.40 $($b.Count)"
 Compare-Object $a $b|Sort-Object InputObject|%{if($_.SideIndicator -eq '=>'){"  + $($_.InputObject)"}else{"  - $($_.InputObject)"}}}
# clean unzip + payload hashes
foreach($p in $pk){$d="$v\clean\$p";[IO.Compression.ZipFile]::ExtractToDirectory("$out\$p-0.40.zip",$d)
 $hip="$d\DLSS5-AMD\native-game-tiled-assets\HIP"
 $lines=@(foreach($a in 'gfx1200','gfx1201'){Get-ChildItem "$hip\$a" -Filter *.hsaco|Sort-Object Name|%{"$((Get-FileHash $_.FullName).Hash.ToLower())  $a/$($_.Name)"}})
 $same=(Compare-Object $lines @(Get-Content D:\DLSSNR-Lab\release-040\HIP-SHA256SUMS)) -eq $null
 $bin=if(Test-Path "$d\dlss5-amd.addon64"){"addon $((Get-FileHash "$d\dlss5-amd.addon64").Hash.Substring(0,8))"}else{"runtime $((Get-FileHash "$d\LmxxfNrRuntime.dll").Hash.Substring(0,8)) host $((Get-FileHash "$d\dxgi.dll").Hash.Substring(0,8)) SUMS $((Get-FileHash "$hip\SHA256SUMS").Hash.Substring(0,8))"}
 "$p : $bin modules=$($lines.Count) manifest_same=$same configs=$((Get-ChildItem "$d\DLSS5-AMD" -File|%{$_.Name}) -join ',')"}
# RE9 replay: package runtime + package modules + package shaders, no config file (= old harness "no file" side)
$d="$v\clean\OptiScaler-REFramework-DLSS5-AMD";$r="$v\rt";New-Item -ItemType Directory "$r\modules" -Force|Out-Null
Copy-Item "$d\DLSS5-AMD\native-game-tiled-assets\HIP\*" "$r\modules" -Recurse -Force;Copy-Item "$d\LmxxfNrRuntime.dll" $r
$env:LMXXF_WEIGHTS_DIR='D:\DLSSNR-Lab\zero-copy-io-20260928\assets';New-Item -ItemType Directory -Force "$r\shaders"|Out-Null;Copy-Item 'D:\DLSSNR-Lab\hip-backend\fusion-round3\shaders\*' "$r\shaders" -Force  # runtime looks in <dll>\shaders; same set as config-layers rt9.ps1 (reference hashes)
$env:DLSS5_HIP_PDL='1';$env:DLSS5_HIP_VIT_STREAM='3';$env:DLSS5_VIT_ADAPTIVE='0';$env:DLSS5_HIP_SWIN_RUN='1'
foreach($h in 900,1080){foreach($i in 1,2){$env:DLSS5_NETWORK_HEIGHT="$h"
 & 'D:\DLSSNR-Lab\re9-runtime-flags-20260926\in\rt_bench.exe' "$r\LmxxfNrRuntime.dll" "$r\modules" '1707x961' 12 1 *> "$v\rt-$h-$i.log";$e=$LASTEXITCODE
 "RE9 replay $h run$i exit=$e hash=$([regex]::Match((Get-Content "$v\rt-$h-$i.log" -Raw),'hash=([0-9a-f]+)').Groups[1].Value)"}}
Remove-Item Env:DLSS5_NETWORK_HEIGHT
# runtime-smoke in the package layout (reads DLSS5-AMD\default-config.txt)
& 'D:\DLSSNR-Lab\re9-presr\runtime-smoke.exe' "$d\LmxxfNrRuntime.dll" "$d\DLSS5-AMD\native-game-tiled-assets\HIP" 32 *> "$v\smoke.log";"SMOKE exit=$LASTEXITCODE";Get-Content "$v\smoke.log"|Select-String 'flags|errors|gpu'
# upgrade: unzip 0.40 over an unpacked 0.39 that has user files
foreach($p in $pk){$u="$v\upgrade\$p";[IO.Compression.ZipFile]::ExtractToDirectory("$out\$p-0.39.zip",$u)
 $c="$u\DLSS5-AMD\custom-config.txt";$n="$u\DLSS5-AMD\native-game-flags.txt"
 Set-Content $c "DLSS5_MULTI_PASS=2`r`n# user marker" -Encoding UTF8;Add-Content $n "`r`n# user edit marker`r`nDLSS5_SHOW_FPS=0"
 $hc=(Get-FileHash $c).Hash;$hn=(Get-FileHash $n).Hash
 $z=[IO.Compression.ZipFile]::OpenRead("$out\$p-0.40.zip");try{foreach($e in $z.Entries){if(!$e.Name){continue};$t=Join-Path $u $e.FullName;New-Item -ItemType Directory -Force (Split-Path $t)|Out-Null;[IO.Compression.ZipFileExtensions]::ExtractToFile($e,$t,$true)}}finally{$z.Dispose()}
 "UPGRADE $p custom_untouched=$((Get-FileHash $c).Hash -eq $hc) native_untouched=$((Get-FileHash $n).Hash -eq $hn) default_config=$(Test-Path "$u\DLSS5-AMD\default-config.txt") template=$(Test-Path "$u\DLSS5-AMD\custom-config.template.txt")"}
'VERIFY_DONE'

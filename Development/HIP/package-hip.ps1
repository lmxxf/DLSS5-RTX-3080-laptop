param([string]$Version='0.20',[string]$Modules='ffnh2-modules',[string]$Addon='native-pinline.addon64',
 [string]$AddonSha='8D5A218FF26FC6E89B01DB77E1BEADC1B2C028C4DC4066D40D39AEC243270343',[string]$Base='Magpie-DLSS5-AMD-0.15-900P',[switch]$VerifyOnly,[string]$OutputDirectory='D:\給網友打包')
# Builds the two HIP user packages on the AMD box from the last Magpie staging directory (weights already f16 where exact):
#   D:\DLSSNR-Lab\DLSS5-AMD-<v>\          game edition (d3d12.dll + dlss5-amd.addon64 + DLSS5-AMD\{flags, HIP\*.hsaco, assets, logs})
#   D:\DLSSNR-Lab\Magpie-DLSS5-AMD-<v>\   Magpie edition (the 0.15-900P bundle minus DLSS5-D3D12-721/enable-game-sdk721.txt, plus HIP\, new DLL/flags/README)
# Inputs uploaded next to this script: hip-game-flags.txt, hip-magpie-flags.txt, package-README-hip.txt, package-README-magpie-hip.txt.
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend";$utf8=New-Object Text.UTF8Encoding($false)
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$addon="$r\stellarblade-hip\$Addon";if((Get-FileHash $addon).Hash -ne $AddonSha){throw 'addon hash mismatch'}
$mods=@(Get-ChildItem "$r\$Modules" -Filter '*.hsaco');if($mods.Count -ne 24){throw 'expected 24 modules'}
$base="$lab\$Base";if(!(Test-Path "$base\DLSS5-AMD\native-game-tiled-assets")){throw 'base staging missing'}
$loader="$game\d3d12.dll";if((Get-FileHash $loader).Hash -ne (Get-FileHash "$base\dxgi.dll").Hash){throw 'ReShade loader differs between game and base bundle'}
function Sums($stage){$lines=@(Get-ChildItem $stage -Recurse -File|Where-Object{$_.Name -ne 'SHA256SUMS.txt'}|Sort-Object FullName|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLowerInvariant()+'  '+$_.FullName.Substring($stage.Length+1).Replace('\','/')});[IO.File]::WriteAllLines("$stage\SHA256SUMS.txt",$lines,$utf8);$lines.Count}
function Zip($stage){New-Item -ItemType Directory -Force $OutputDirectory|Out-Null;$zip=Join-Path $OutputDirectory ((Split-Path $stage -Leaf)+'.zip');if(Test-Path $zip){Remove-Item $zip};Add-Type -AssemblyName System.IO.Compression.FileSystem;[IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip,[IO.Compression.CompressionLevel]::Fastest,$true)
 $lines=[IO.File]::ReadAllLines("$stage\SHA256SUMS.txt");$archive=[IO.Compression.ZipFile]::OpenRead($zip);$n=0
 try{$prefix=(Split-Path $stage -Leaf)+'/';$entries=@{};foreach($e in $archive.Entries){$entries[$e.FullName.Replace('\','/')]=$e}
  foreach($line in $lines){$hash=$line.Substring(0,64);$name=$line.Substring(66);$e=$entries[$prefix+$name];if(!$e){throw "missing archive entry $name"};$s=$e.Open();$sha=[Security.Cryptography.SHA256]::Create();try{$actual=([BitConverter]::ToString($sha.ComputeHash($s))).Replace('-','').ToLowerInvariant()}finally{$s.Dispose();$sha.Dispose()};if($actual -ne $hash){throw "archive hash mismatch $name"};$n++}}finally{$archive.Dispose()}
 $zh=(Get-FileHash $zip).Hash.ToLowerInvariant();[IO.File]::WriteAllText("$zip.sha256",$zh+'  '+(Split-Path $zip -Leaf)+"`n",$utf8);"$(Split-Path $zip -Leaf) files=$n bytes=$((Get-Item $zip).Length) sha256=$zh"}
function Common($lab5,$flagsName){# The add-on resolves the module directory as <assets>\HIP when DLSS5_HIP_MODULES is absent (native_hip_network.h), so the kernels live under the asset folder.
 Remove-Item "$lab5\HIP" -Recurse -Force -ErrorAction SilentlyContinue;New-Item -ItemType Directory -Force "$lab5\native-game-tiled-assets\HIP","$lab5\logs"|Out-Null;foreach($m in $mods){Copy-Item $m.FullName "$lab5\native-game-tiled-assets\HIP\$($m.Name)" -Force}
 Copy-Item "$r\$flagsName" "$lab5\native-game-flags.txt" -Force;foreach($n in 'continuous-every-frame.txt','temporal-history.txt'){[IO.File]::WriteAllText("$lab5\$n","1`n",$utf8)}
 Remove-Item "$lab5\enable-game-sdk721.txt" -ErrorAction SilentlyContinue;Get-ChildItem "$lab5\logs" -File|Remove-Item -Force;[IO.File]::WriteAllText("$lab5\logs\.keep","",$utf8)}
if(!$VerifyOnly){
 # game edition
 $g="$lab\DLSS5-AMD-$Version";if(Test-Path $g){Remove-Item $g -Recurse -Force}
 New-Item -ItemType Directory "$g\DLSS5-AMD"|Out-Null
 Copy-Item $loader "$g\d3d12.dll";Copy-Item $addon "$g\dlss5-amd.addon64"
 Copy-Item "$base\DLSS5-AMD\native-game-tiled-assets" "$g\DLSS5-AMD\native-game-tiled-assets" -Recurse
 Common "$g\DLSS5-AMD" 'hip-game-flags.txt'
 Copy-Item "$r\package-README-hip.txt" "$g\README.txt"
 foreach($lic in 'ReShade-LICENSE.txt','MinHook-LICENSE.txt'){$src=Get-ChildItem $lab -Recurse -Filter $lic -ErrorAction SilentlyContinue|Select-Object -First 1;if($src){Copy-Item $src.FullName "$g\$lic"}else{Write-Warning "$lic not found"}}
 # magpie edition
 $m="$lab\Magpie-DLSS5-AMD-$Version";if(Test-Path $m){Remove-Item $m -Recurse -Force}
 Copy-Item $base $m -Recurse
 Remove-Item "$m\DLSS5-D3D12-721" -Recurse -Force;Remove-Item "$m\SHA256SUMS.txt" -Force
 Get-ChildItem $m -Recurse -File|Where-Object{$_.Name -match '\.addon64\.|\.bak$|\.log$|^GpuDebuggingLog\.txt$|\.dmp$'}|Remove-Item -Force
 Get-ChildItem $m -Recurse -Directory|Where-Object{$_.Name -in @('logs','shader-cache')}|Sort-Object{$_.FullName.Length} -Descending|Remove-Item -Recurse -Force
 Copy-Item $addon "$m\dlss5-amd.addon64" -Force
 Common "$m\DLSS5-AMD" 'hip-magpie-flags.txt'
 Copy-Item "$r\package-README-magpie-hip.txt" "$m\README.txt" -Force
 [IO.File]::WriteAllText("$m\DLSS5-AMD-VERSION.txt","DLSS5-AMD $Version (HIP backend, gfx1201) addon sha256 $AddonSha`n",$utf8)
 $cfg=Get-Content "$m\config\config.json" -Raw -Encoding UTF8;$null=$cfg|ConvertFrom-Json;if(!$cfg.Contains('XeSS_FrameGeneration_x2_ZeroMV')){throw 'FG preset missing'}
 foreach($stage in $g,$m){$flags=Get-Content "$stage\DLSS5-AMD\native-game-flags.txt";if($flags -notcontains 'DLSS5_HIP_FAST=1'){throw 'HIP flag missing'};if($flags -match '^DLSS5_HIP_MODULES=|^DLSS5_(DEBUG_DUMPS|BLACK_PROBE)=1$'){throw 'bad flags'};"$(Split-Path $stage -Leaf): files="+(Sums $stage)}
}
foreach($stage in "$lab\DLSS5-AMD-$Version","$lab\Magpie-DLSS5-AMD-$Version"){Zip $stage}

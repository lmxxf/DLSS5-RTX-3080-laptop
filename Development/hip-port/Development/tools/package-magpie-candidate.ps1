param([string]$Version='0.26',[string]$Base='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23',
 [string]$Addon='D:\DLSSNR-Lab\c256-frag-src\native-c256-fragment.addon64',
 [string]$AddonSha='f5d3f7348e42f362a0db4233814e1b2d8c4842de0d1196620a40bbc299adde75',
 [string]$Modules='D:\DLSSNR-Lab\c256-frag-production-modules',
 [string]$OutputDirectory='D:\給網友打包',[string]$CodecDecodePath='D:\DLSSNR-Lab\native_codec_decode.hlsl',[string]$ConfigDirectory=(Join-Path $PSScriptRoot '..\..\scripts'))
$ErrorActionPreference='Stop';$utf8=New-Object Text.UTF8Encoding($false)
if(!(Test-Path "$ConfigDirectory\hip-magpie-flags.txt")){throw 'Missing repository default configuration'}
$stage=Join-Path $OutputDirectory "Magpie-DLSS5-AMD-$Version"
if((Test-Path $stage) -or (Test-Path "$stage.zip")){throw 'Output already exists'}
if((Get-FileHash $Addon).Hash -ne $AddonSha){throw 'Candidate hash mismatch'}
if(!(Test-Path $CodecDecodePath)){throw 'Upload current shaders/native_codec_decode.hlsl before packaging'}
# Validate the archived baseline before copying; never read a live Magpie installation.
foreach($line in [IO.File]::ReadAllLines("$Base\SHA256SUMS.txt")){
 if((Get-FileHash (Join-Path $Base $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Baseline checksum mismatch'}
}
New-Item -ItemType Directory -Force $OutputDirectory|Out-Null
Copy-Item $Base $stage -Recurse
Copy-Item $Addon "$stage\dlss5-amd.addon64" -Force
Copy-Item $CodecDecodePath "$stage\DLSS5-AMD\native-game-tiled-assets\native_codec_decode.hlsl" -Force
Copy-Item 'D:\DLSSNR-Lab\package-README-magpie-hip.txt' "$stage\README.txt" -Force
[IO.File]::WriteAllText("$stage\DLSS5-AMD-VERSION.txt","DLSS5-AMD $Version Magpie (HIP gfx1200/gfx1201) addon sha256 $AddonSha`n",$utf8)
$hip='DLSS5-AMD\native-game-tiled-assets\HIP'
Remove-Item "$stage\$hip" -Recurse -Force
New-Item -ItemType Directory -Force "$stage\$hip"|Out-Null
foreach($arch in 'gfx1200','gfx1201'){
 New-Item -ItemType Directory -Force "$stage\$hip\$arch"|Out-Null
 Copy-Item "$Modules\$arch\*.hsaco" "$stage\$hip\$arch"
}
Copy-Item 'D:\DLSSNR-Lab\HIP-API-LICENSE.txt' "$stage\HIP-API-LICENSE.txt"
foreach($arch in 'gfx1200','gfx1201'){
 if(@(Get-ChildItem "$stage\$hip\$arch\*.hsaco").Count -ne 24){throw "Expected 24 modules for $arch"}
}
foreach($f in Get-ChildItem $Modules -Recurse -File -Filter *.hsaco){
 $rel=$f.FullName.Substring($Modules.Length+1)
 if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash "$stage\$hip\$rel").Hash){throw 'Module copy mismatch'}
}
foreach($rel in 'DLSS5-AMD\logs','DLSS5-AMD\native-game-tiled-assets\shader-cache'){
 if(Test-Path "$stage\$rel"){Remove-Item "$stage\$rel" -Recurse -Force}
}
$flag="$stage\DLSS5-AMD\native-game-flags.txt"
Copy-Item "$ConfigDirectory\hip-magpie-flags.txt" $flag -Force
$allowed=@('DLSS5-AMD\native-game-tiled-assets\native_codec_decode.hlsl','HIP-API-LICENSE.txt','dlss5-amd.addon64','README.txt','DLSS5-AMD-VERSION.txt','DLSS5-AMD\native-game-flags.txt','SHA256SUMS.txt')
foreach($f in Get-ChildItem $stage -Recurse -File){
 $rel=$f.FullName.Substring($stage.Length+1)
 if($rel -notlike "$hip\*" -and $rel -notin $allowed -and (Get-FileHash $f.FullName).Hash -ne (Get-FileHash (Join-Path $Base $rel)).Hash){throw "Unexpected changed payload $rel"}
}
if((Get-FileHash "$stage\dlss5-amd.addon64").Hash -ne $AddonSha){throw 'Staged addon mismatch'}
function Sums($stage){$lines=@(Get-ChildItem $stage -Recurse -File|Where-Object{$_.Name -ne 'SHA256SUMS.txt'}|Sort-Object FullName|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLowerInvariant()+'  '+$_.FullName.Substring($stage.Length+1).Replace('\','/')});[IO.File]::WriteAllLines("$stage\SHA256SUMS.txt",$lines,$utf8);$lines.Count}
function Zip($stage){New-Item -ItemType Directory -Force $OutputDirectory|Out-Null;$zip=Join-Path $OutputDirectory ((Split-Path $stage -Leaf)+'.zip');if(Test-Path $zip){Remove-Item $zip};Add-Type -AssemblyName System.IO.Compression.FileSystem;[IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip,[IO.Compression.CompressionLevel]::Fastest,$true)
 $lines=[IO.File]::ReadAllLines("$stage\SHA256SUMS.txt");$archive=[IO.Compression.ZipFile]::OpenRead($zip);$n=0
 try{$prefix=(Split-Path $stage -Leaf)+'/';$entries=@{};foreach($e in $archive.Entries){$entries[$e.FullName.Replace('\','/')]=$e}
  foreach($line in $lines){$hash=$line.Substring(0,64);$name=$line.Substring(66);$e=$entries[$prefix+$name];if(!$e){throw "missing archive entry $name"};$s=$e.Open();$sha=[Security.Cryptography.SHA256]::Create();try{$actual=([BitConverter]::ToString($sha.ComputeHash($s))).Replace('-','').ToLowerInvariant()}finally{$s.Dispose();$sha.Dispose()};if($actual -ne $hash){throw "archive hash mismatch $name"};$n++}}finally{$archive.Dispose()}
 $zh=(Get-FileHash $zip).Hash.ToLowerInvariant();[IO.File]::WriteAllText("$zip.sha256",$zh+'  '+(Split-Path $zip -Leaf)+"`n",$utf8);"$(Split-Path $zip -Leaf) files=$n bytes=$((Get-Item $zip).Length) sha256=$zh"}

& 'D:\DLSSNR-Lab\compile_fit_shaders.exe' "$stage\DLSS5-AMD\native-game-tiled-assets"
if($LASTEXITCODE){throw 'Runtime shader compile/reflection validation failed'}
Sums $stage
Zip $stage

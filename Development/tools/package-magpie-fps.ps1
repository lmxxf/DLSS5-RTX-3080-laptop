# Magpie bundle builder. Historical filename retained so repeat packaging uses the same tool.
param(
 [switch]$VerifyOnly,
 [switch]$Repack,
 [string]$Version='0.15',
 [string]$SourceVersion='0.14',
 [string]$Payload='D:\DLSSNR-Lab\release-0.15',
 [string]$ShaderOverlay='',
 [string]$ExpectedAddon='6FB89C030CEC9AC62731D616494A24E50D68364533E5CD21B92A6AF28D8A313E'
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$lab='D:\DLSSNR-Lab'
$source=Join-Path $lab "Magpie-DLSS5-AMD-$SourceVersion"
$stage=Join-Path $lab "Magpie-DLSS5-AMD-$Version"
$zip="$stage.zip"
$installed='D:\Magpie-DLSS5\Magpie-Experimental-x64\Magpie-Experimental-x64'
$utf8=New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
if(!$VerifyOnly){
 if(((Test-Path $stage) -or (Test-Path $zip)) -and !$Repack){throw 'Output exists; inspect before replacing or use -Repack.'}
 $addon=Join-Path $installed 'dlss5-amd.addon64'
 if((Get-FileHash $addon).Hash -ne $ExpectedAddon){throw 'Installed addon differs from the game-tested build.'}
 # Use the tested host and dependencies; no running installation is modified.
 foreach($name in @('Magpie.exe','dxgi.dll','amd_fidelityfx_loader_dx12.dll','amd_fidelityfx_upscaler_dx12.dll','libxess_fg.dll','effects\FSR4\FSR4_SR.hlsl')){
  if((Get-FileHash (Join-Path $source $name)).Hash -ne (Get-FileHash (Join-Path $installed $name)).Hash){throw "Base bundle differs from tested host: $name"}
 }
 $current=Get-Content "$env:LOCALAPPDATA\Magpie\config\v4\config.json" -Raw -Encoding UTF8 | ConvertFrom-Json
 $groups=@($current.scalingModes | Where-Object name -eq 'DLSS5-AMD')
 if($groups.Count -ne 1){throw 'Expected one tested DLSS5-AMD preset.'}
 $effects=$groups[0].effects
 if($effects.Count -ne 3 -or $effects[0].name -ne 'FSR3\FSR3_SR' -or $effects[1].name -ne 'FSR4\FSR4_SR' -or $effects[2].name -ne 'XeSSFG\XeSS_FrameGeneration_x2_ZeroMV'){throw 'Unexpected tested effect order.'}
 if([int]$effects[0].scalingType -ne 0 -or [int]$effects[1].scalingType -ne 3){throw 'Expected original-size FSR3 and screen-fill FSR4.'}
 if([int]$effects[0].parameters.opticalFlowMethod -ne 1 -or [int]$effects[1].parameters.opticalFlowMethod -ne 0 -or [int]$effects[2].parameters.opticalFlowMethod -ne 0){throw 'Expected AMDOF only on the DLSS5/FSR3 stage; FSR4 and XeSS FG must use None.'}
 if($effects[0].scale -and ($effects[0].scale.x -ne 1 -or $effects[0].scale.y -ne 1)){throw 'FSR3 is not original size.'}
 foreach($name in @('native_codec_encode.hlsl','native_codec_decode.hlsl','native_temporal_coordinates.hlsl')){
  if((Get-FileHash (Join-Path $Payload $name)).Hash -ne (Get-FileHash (Join-Path $installed "DLSS5-AMD\native-game-tiled-assets\$name")).Hash){throw "Repository shader differs from tested install: $name"}
 }
 $shaderFiles=@()
 if($ShaderOverlay){
  $shaderFiles=@(Get-ChildItem $ShaderOverlay -File | Where-Object {$_.Extension -in @('.cso','.hlsl','.hlsli')})
  if(!$shaderFiles.Count){throw 'Shader overlay is empty.'}
  foreach($file in $shaderFiles){
   $live=Join-Path $installed ('DLSS5-AMD\native-game-tiled-assets\'+$file.Name)
   if(!(Test-Path $live) -or (Get-FileHash $live).Hash -ne (Get-FileHash $file.FullName).Hash){throw "Shader overlay differs from tested install: $($file.Name)"}
  }
 }
 $flags=Get-Content (Join-Path $Payload 'magpie-flags.txt')
 foreach($flag in @('DLSS5_FIT_INPUT=1','DLSS5_SHOW_FPS=1','DLSS5_CODEC_SRGB=1')){if($flags -notcontains $flag){throw "Missing release flag $flag"}}
 if($Version -eq '0.15-900P' -and ($flags -notcontains 'DLSS5_NETWORK_HEIGHT=900' -or !$ShaderOverlay)){throw '900P requires matching shaders and height=900.'}
 if($flags -match '^DLSS5_(DEBUG_DUMPS|BLACK_PROBE|GAME_PROBE)=1$'){throw 'Diagnostic flag enabled.'}
 $readme=Get-Content (Join-Path $Payload 'package-README-magpie.txt') -Raw -Encoding UTF8
 if(!$readme.Contains("DLSS5-AMD $Version")){throw 'README version differs.'}
 if($Repack){
  if($Version -notmatch '^0\.[0-9]+(-(720|900|1080)P)?$' -or $stage -eq $source){throw 'Invalid repack target.'}
  $previous=Join-Path $Payload 'previous-package'
  if(Test-Path $previous){throw 'Previous repack backup already exists; inspect it first.'}
  New-Item -ItemType Directory -Path $previous | Out-Null
  if(Test-Path (Join-Path $stage 'SHA256SUMS.txt')){Copy-Item (Join-Path $stage 'SHA256SUMS.txt') (Join-Path $previous 'SHA256SUMS.txt')}
  if(Test-Path $zip){Move-Item $zip $previous}
  if(Test-Path "$zip.sha256"){Move-Item "$zip.sha256" $previous}
  if(Test-Path $stage){Remove-Item $stage -Recurse -Force}
 }
 Copy-Item $source $stage -Recurse
 Copy-Item $addon (Join-Path $stage 'dlss5-amd.addon64') -Force
 Copy-Item (Join-Path $Payload 'package-README-magpie.txt') (Join-Path $stage 'README.txt') -Force
 Copy-Item (Join-Path $Payload 'magpie-flags.txt') (Join-Path $stage 'DLSS5-AMD\native-game-flags.txt') -Force
 foreach($name in @('native_codec_encode.hlsl','native_codec_decode.hlsl','native_temporal_coordinates.hlsl')){
  Copy-Item (Join-Path $Payload $name) (Join-Path $stage "DLSS5-AMD\native-game-tiled-assets\$name") -Force
 }
 foreach($file in $shaderFiles){Copy-Item $file.FullName (Join-Path $stage ('DLSS5-AMD\native-game-tiled-assets\'+$file.Name)) -Force}
 # Retain the portable baseline, replacing only its DLSS5 preset with the game-tested one.
 $configPath=Join-Path $stage 'config\config.json'
 $cfg=Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
 $index=-1
 for($i=0;$i -lt $cfg.scalingModes.Count;$i++){if($cfg.scalingModes[$i].name -eq 'DLSS5-AMD'){$index=$i;$cfg.scalingModes[$i]=$groups[0]}}
 if($index -lt 0){throw 'Portable preset missing.'}
 $cfg.profiles[0].scalingMode=$index
 [IO.File]::WriteAllText($configPath,($cfg | ConvertTo-Json -Depth 50),$utf8)
 Get-ChildItem $stage -Recurse -File | Where-Object {$_.Name -match '\.addon64\.|\.bak$|\.log$|^GpuDebuggingLog\.txt$|^SHA256SUMS(\.txt)?$|\.dmp$'} | Remove-Item -Force
 Get-ChildItem $stage -Recurse -Directory | Where-Object {$_.Name -in @('logs','shader-cache')} | Sort-Object {$_.FullName.Length} -Descending | Remove-Item -Recurse -Force
 [IO.File]::WriteAllText((Join-Path $stage 'DLSS5-AMD-VERSION.txt'),"DLSS5-AMD $Version`naddon-sha256=$($ExpectedAddon.ToLowerInvariant())`n",$utf8)
 $lines=@(Get-ChildItem $stage -Recurse -File | Sort-Object FullName | ForEach-Object {
  (Get-FileHash $_.FullName).Hash.ToLowerInvariant()+'  '+$_.FullName.Substring($stage.Length+1).Replace('\','/')
 })
 [IO.File]::WriteAllLines((Join-Path $stage 'SHA256SUMS.txt'),$lines,$utf8)
 [IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip,[IO.Compression.CompressionLevel]::Fastest,$true)
}
$lines=[IO.File]::ReadAllLines((Join-Path $stage 'SHA256SUMS.txt'))
$archive=[IO.Compression.ZipFile]::OpenRead($zip)
try{
 $prefix=(Split-Path $stage -Leaf)+'/'
 $entries=@{};foreach($item in $archive.Entries){$entries[$item.FullName.Replace('\','/')]=$item}
 $verified=0
 foreach($line in $lines){
  $hash=$line.Substring(0,64);$name=$line.Substring(66)
  $entry=$entries[$prefix+$name];if(!$entry){throw "Missing archive entry: $name"}
  $stream=$entry.Open();$sha=[Security.Cryptography.SHA256]::Create()
  try{$actual=([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
  finally{$stream.Dispose();$sha.Dispose()}
  if($actual -ne $hash){throw "Archive hash mismatch: $name"};$verified++
 }
 $fileCount=@($archive.Entries | Where-Object {$_.Name -ne ''}).Count
 if($fileCount -ne $verified+1){throw 'Archive has unlisted files.'}
}finally{$archive.Dispose()}
$zipHash=(Get-FileHash $zip).Hash
[IO.File]::WriteAllText("$zip.sha256",$zipHash.ToLowerInvariant()+'  '+(Split-Path $zip -Leaf)+"`n",$utf8)
Write-Output "VERIFIED_FILES=$verified"
Write-Output "ZIP=$zip"
Write-Output "BYTES=$((Get-Item $zip).Length)"
Write-Output "SHA256=$zipHash"

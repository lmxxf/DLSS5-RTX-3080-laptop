param([string]$Version='0.36',[string]$SourceCommit='',[string]$ConfigDirectory='D:\DLSSNR-Lab\release-036\scripts',[switch]$Resume)
# 0.36: three full packages from the 0.35 baselines. Payload per results/fusion-round3-20260928/package-036-checklist.md:
# regular/Magpie add-on d2290ad7 (ACO-lineup cuts, float FMA activation = new bit-exact baseline, DLSS5_DIRECT_IO input direct-write,
# C256/C512/C64/C128/C32 fused blocks, DLSS5_FRAME_STATS), 60 modules (30 per architecture) from the frozen fusion-round3 payload,
# RE9 runtime 7ce2bc21 (host aa3761f2 unchanged, taken from the 0.35 RE9 baseline), shader sources from the final tree
# (native_game_rgb_input.hlsl 5be59a41 matches the direct-write add-on). Flags: regular/Magpie DLSS5_DIRECT_IO=1, RE9 without it.
$ErrorActionPreference='Stop'
if(!$SourceCommit){throw 'SourceCommit required'}
$out='D:\給網友打包';$lab='D:\DLSSNR-Lab\release-036';$utf8=New-Object Text.UTF8Encoding($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$final='D:\DLSSNR-Lab\hip-backend\fusion-round3'
$regularSha='d2290ad7426967edfd566b5c53e1e2ae580a41463b08594375079fb7b84abfdf'
$hostSha='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2'
$runtimeSha='7ce2bc21cde9c5c5f026ebd96eefa72b4e18699aad4c30239bdc2af5776bcfdc'
$inputShaderSha='5be59a4130e66e9f9f4d370843ef080e0783042d1f730b7a06c072421c92c2b6'
$addonPath="$final\dlss5-amd.addon64";$runtimePath="$final\re9-runtime-final\LmxxfNrRuntime.dll"
$moduleRoot="$final\re9-runtime-final\modules";$shaderSrc="$final\shaders"
function CheckHash($path,$sha){if((Get-FileHash $path).Hash -ne $sha){throw "HASH mismatch $path"}}
function WriteUtf8($path,$text){[IO.File]::WriteAllText($path,$text,$utf8)}
function HasLine($path,$line){Select-String -Path $path -Pattern ('^'+[regex]::Escape($line)+'\s*$') -Quiet}
function SetIni($text,$section,$key,$value){
 $pattern='(?ms)^\['+[regex]::Escape($section)+'\]\r?\n.*?(?=^\[|\z)'
 $m=[regex]::Match($text,$pattern)
 if(!$m.Success){return $text+"`r`n[$section]`r`n$key=$value`r`n"}
 $part=$m.Value;$kp='(?m)^'+[regex]::Escape($key)+'=[^\r\n]*'
 if([regex]::IsMatch($part,$kp)){$part=[regex]::Replace($part,$kp,"$key=$value")}else{$part=$part.TrimEnd()+"`r`n$key=$value`r`n"}
 return $text.Substring(0,$m.Index)+$part+$text.Substring($m.Index+$m.Length)
}
function VerifyZip($zip,$sums){
 $z=[IO.Compression.ZipFile]::OpenRead($zip)
 try{
  $entries=@{};foreach($e in $z.Entries){if($entries.ContainsKey($e.FullName)){throw 'Duplicate ZIP entry'};$entries[$e.FullName.Replace('\','/')]=$e}
  foreach($line in $sums){$name=$line.Substring(66);$e=$entries[$name];if(!$e){throw "Missing ZIP entry $name"};$s=$e.Open();$h=[Security.Cryptography.SHA256]::Create();try{$got=([BitConverter]::ToString($h.ComputeHash($s))).Replace('-','')}finally{$s.Dispose();$h.Dispose()};if($got -ne $line.Substring(0,64)){throw "ZIP mismatch $name"}}
  if($entries.Count -ne $sums.Count+1){throw 'ZIP extra/missing files'}
 }finally{$z.Dispose()}
}
$busy=Get-Process re9,SB-Win64-Shipping,LOP-Win64-Shipping,Magpie,OnimushaWotS,SandFall* -ErrorAction SilentlyContinue
if($busy){throw "Game running ($($busy.Name -join ',')); shader validation and RE9 smoke need the GPU"}
CheckHash $addonPath $regularSha
CheckHash $runtimePath $runtimeSha
CheckHash "$shaderSrc\native_game_rgb_input.hlsl" $inputShaderSha
foreach($n in 'SOURCE-README.txt','HOST-LICENSE.txt','CORE-LICENSE.txt'){if(!(Test-Path "$lab\$n")){Copy-Item "D:\DLSSNR-Lab\release-035\$n" "$lab\$n"}}
if(!(Test-Path "$lab\re9-presr-source.tar.gz")){throw 'regenerated re9-presr-source.tar.gz missing'}
# Module payload: the frozen 60 modules, checked one by one against the release manifest (HIP-SHA256SUMS from the checklist).
$expected=@{};foreach($line in Get-Content "$lab\HIP-SHA256SUMS"){$expected[$line.Substring(66)]=$line.Substring(0,64)}
if($expected.Count -ne 60){throw 'Manifest count'}
$changes=@()
foreach($arch in 'gfx1200','gfx1201'){foreach($f in Get-ChildItem "$moduleRoot\$arch" -Filter *.hsaco){
 $rel="$arch/$($f.Name)";$sha=(Get-FileHash $f.FullName).Hash.ToLower()
 if($expected[$rel] -ne $sha){throw "Module not in manifest or hash differs: $rel"}
 $changes+=[pscustomobject]@{source=$f.FullName;target="DLSS5-AMD/native-game-tiled-assets/HIP/$rel";sha256=$sha}
}}
if($changes.Count -ne 60){throw 'Module count'}
WriteUtf8 "$lab\payload.json" ($changes|ConvertTo-Json)
$variants=@(@{kind='magpie';prefix='Magpie-DLSS5-AMD';flags='hip-magpie-flags.txt';base='0.35'},@{kind='optiscaler';prefix='OptiScaler-DLSS5-AMD';flags='hip-game-flags.txt';base='0.35'},@{kind='re9';prefix='OptiScaler-REFramework-DLSS5-AMD';flags='re9-presr.ini';base='0.35'})
$results=@()
foreach($v in $variants){
 $name="$($v.prefix)-$Version";$stage=Join-Path $out $name;$zip="$stage.zip";$baseline=Join-Path $out "$($v.prefix)-$($v.base).zip"
 if(!(Test-Path $baseline)){$baseline=Join-Path "$out\history" "$($v.prefix)-$($v.base).zip"}
 if(Test-Path $zip){if(!$Resume){throw "Output exists $zip"};$sums=@(Get-Content "$stage\SHA256SUMS.txt");VerifyZip $zip $sums}
 else{
  if(Test-Path $stage){throw "Incomplete stage exists; inspect before retry: $stage"}
  $baselineSha=((Get-Content "$baseline.sha256" -Raw).Trim() -split '\s+')[0]
  CheckHash $baseline $baselineSha
  [IO.Compression.ZipFile]::ExtractToDirectory($baseline,$stage)
  foreach($line in Get-Content "$stage\SHA256SUMS.txt"){$exp=$line.Substring(0,64);$relative=$line.Substring(66);CheckHash (Join-Path $stage $relative) $exp}
  Write-Output "BASE VERIFIED $name ($baseline)"
  $assets="$stage\DLSS5-AMD\native-game-tiled-assets"
  foreach($i in $changes){Copy-Item $i.source (Join-Path $stage $i.target) -Force;CheckHash (Join-Path $stage $i.target) $i.sha256}
  foreach($arch in 'gfx1200','gfx1201'){if(@(Get-ChildItem "$assets\HIP\$arch\*.hsaco").Count -ne 30){throw 'Architecture module count'}}
  if(@(Get-ChildItem "$assets\HIP" -Recurse -Filter *.hsaco).Count -ne 60){throw 'Dual architecture count'}
  # Shader sources: every shipped .hlsl/.hlsli is refreshed from the final tree (flat in the package, dx12-network\ in the tree).
  foreach($f in Get-ChildItem $assets -File|Where-Object{$_.Extension -in '.hlsl','.hlsli'}){
   $src=Join-Path $shaderSrc $f.Name;if(!(Test-Path $src)){$src=Join-Path "$shaderSrc\dx12-network" $f.Name}
   if(!(Test-Path $src)){throw "No final source for shipped shader $($f.Name)"}
   Copy-Item $src $f.FullName -Force
  }
  CheckHash "$assets\native_game_rgb_input.hlsl" $inputShaderSha
  if($v.kind -ne 're9'){
   Copy-Item $addonPath "$stage\dlss5-amd.addon64" -Force;CheckHash "$stage\dlss5-amd.addon64" $regularSha
   $flags="$stage\DLSS5-AMD\native-game-flags.txt"
   Copy-Item "$ConfigDirectory\$($v.flags)" $flags -Force
   CheckHash $flags (Get-FileHash "$ConfigDirectory\$($v.flags)").Hash
   foreach($f in 'DLSS5_FIT_LARGE=1','DLSS5_HIP_PDL=1','DLSS5_HIP_WAVE_OWNED=1','DLSS5_HIP_C512_M32=1','DLSS5_HIP_VIT_PROJ_N64=1','DLSS5_NETWORK_HEIGHT=auto','DLSS5_HIP_VIT_STREAM=3','DLSS5_DIRECT_IO=1','DLSS5_FRAME_STATS=0','DLSS5_MAKE_RESIDENT_EVERY=60'){if(!(HasLine $flags $f)){throw "flags missing $f"}}
   if($v.kind -eq 'optiscaler'){
    foreach($f in 'DLSS5_PRE_UPSCALE_ASYNC=auto','DLSS5_STRENGTH=auto','DLSS5_VIT_ADAPTIVE=1'){if(!(HasLine $flags $f)){throw "flags missing $f"}}
    # regular package: games that ship their own FSR dll (Cyberpunk 2077) need OptiScaler to leave the FFX inputs to the game dll; a no-op for Stellar Blade
    $ini=[IO.File]::ReadAllText("$stage\OptiScaler.ini");$section=''
    foreach($line in Get-Content "$ConfigDirectory\optiscaler-regular.ini"){if($line -match '^\[(.+)\]'){$section=$matches[1]}elseif($line -match '^([^;#][^=]*)=(.*)$'){$ini=SetIni $ini $section $matches[1] $matches[2]}}
    WriteUtf8 "$stage\OptiScaler.ini" $ini
    if(!(Select-String -Path "$stage\OptiScaler.ini" -Pattern '^EnableFfxInputs=false' -Quiet)){throw 'OptiScaler.ini missing EnableFfxInputs=false'}
   }else{
    if(!(HasLine $flags 'DLSS5_VIT_ADAPTIVE=0')){throw 'magpie flags missing DLSS5_VIT_ADAPTIVE=0'}
    # Magpie's dxgi.dll is ReShade: ship a ReShade.ini with the "press Home" tutorial already dismissed (ReShade fills the other defaults).
    $rs="$stage\ReShade.ini";$rsText=if(Test-Path $rs){[IO.File]::ReadAllText($rs)}else{''}
    WriteUtf8 $rs (SetIni $rsText 'OVERLAY' 'TutorialProgress' '4')
    if(!(HasLine $rs 'TutorialProgress=4')){throw 'ReShade.ini missing TutorialProgress=4'}
   }
  }else{
   foreach($n in 're9-present.addon64','dlss5-amd.addon64','ReShade64.dll','ReShade.ini','ReShadePreset.ini','DLSS5-AMD\re9-present-mode.txt'){if(Test-Path "$stage\$n"){Remove-Item "$stage\$n" -Force}}
   CheckHash "$stage\dxgi.dll" $hostSha
   Copy-Item $runtimePath "$stage\LmxxfNrRuntime.dll" -Force;CheckHash "$stage\LmxxfNrRuntime.dll" $runtimeSha
   # The runtime reads DLSS5-AMD\native-game-flags.txt (found by walking up from the assets directory).
   $flags="$stage\DLSS5-AMD\native-game-flags.txt"
   Copy-Item "$ConfigDirectory\hip-re9-flags.txt" $flags -Force
   foreach($f in 'DLSS5_FIT_LARGE=1','DLSS5_HIP_WAVE_OWNED=1','DLSS5_HIP_C512_M32=1','DLSS5_HIP_VIT_PROJ_N64=1','DLSS5_NETWORK_HEIGHT=auto','DLSS5_HIP_VIT_STREAM=3','DLSS5_FRAME_STATS=0','DLSS5_VIT_ADAPTIVE=0'){if(!(HasLine $flags $f)){throw "re9 flags missing $f"}}
   if(Select-String -Path $flags -Pattern '^DLSS5_DIRECT_IO=' -Quiet){throw 're9 flags must not set DLSS5_DIRECT_IO'}
   $ini=[IO.File]::ReadAllText("$stage\OptiScaler.ini");$section=''
   foreach($line in Get-Content "$ConfigDirectory\re9-presr.ini"){
    if($line -match '^\[(.+)\]'){$section=$matches[1]}elseif($line -match '^([^;#][^=]*)=(.*)$'){$ini=SetIni $ini $section $matches[1] $matches[2]}
   }
   WriteUtf8 "$stage\OptiScaler.ini" $ini
   $moduleSums=@(Get-ChildItem "$assets\HIP" -Recurse -Filter *.hsaco|Sort-Object FullName|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLower()+'  '+$_.FullName.Substring(("$assets\HIP").Length+1).Replace('\','/')})
   [IO.File]::WriteAllLines("$assets\HIP\SHA256SUMS",$moduleSums,$utf8)
   New-Item -ItemType Directory "$stage\sources" -Force|Out-Null
   Copy-Item "$lab\re9-presr-source.tar.gz" "$stage\sources\re9-presr-source.tar.gz" -Force
   Copy-Item "$lab\SOURCE-README.txt" "$stage\sources\README.txt" -Force
   Copy-Item "$lab\HOST-LICENSE.txt" "$stage\OptiScaler-LICENSE.txt" -Force
   Copy-Item "$lab\CORE-LICENSE.txt" "$stage\DLSS5-AMD-LICENSE.txt" -Force
   WriteUtf8 "$stage\UPSTREAM-CREDITS.txt" "Modified OptiScaler host: TheAutomatic https://github.com/TheAutomatic/dlss-5-amd-project/tree/release/1.9.0 (8f71f73bfc836a37936e7cee6701750ad4e8bfec). GPL-3.0 host source is included in sources/re9-presr-source.tar.gz. HIP/core by lmxxf under its included MIT license. PR design credit: TheAutomatic.`n"
   & 'D:\DLSSNR-Lab\re9-presr\runtime-smoke.exe' "$stage\LmxxfNrRuntime.dll" "$assets\HIP" 32;if($LASTEXITCODE){throw 'Staged RE9 runtime validation failed'};$gpuSmoke='passed in staged package'
  }
  foreach($lang in 'zh','en'){$text=[IO.File]::ReadAllText("$ConfigDirectory\package-notes\$($v.kind)-$lang.txt").Replace('@VERSION@',$Version);$file=if($lang -eq 'zh'){'README.txt'}else{'README.en.txt'};WriteUtf8 "$stage\$file" $text}
  if(Test-Path "$stage\build-manifest.json"){Remove-Item "$stage\build-manifest.json" -Force}
  WriteUtf8 "$stage\DLSS5-AMD-VERSION.txt" "$name`r`nsource_commit=$SourceCommit`r`n"
  $meta=[ordered]@{version=$Version;package=$name;kind=$v.kind;baseline=$baseline;baseline_sha256=$baselineSha;configuration=$v.flags;modules=60;source_commit=$SourceCommit;regular_addon_sha256=$(if($v.kind -ne 're9'){$regularSha}else{$null});host_sha256=$(if($v.kind -eq 're9'){$hostSha}else{$null});runtime_sha256=$(if($v.kind -eq 're9'){$runtimeSha}else{$null});input_shader_sha256=$inputShaderSha;gpu_smoke=$(if($v.kind -eq 're9'){$gpuSmoke}else{$null});fit_large=$true;bit_exact_vs_previous=$false;note='float FMA activation: new bit-exact baseline from 0.36'}
  WriteUtf8 "$stage\release.json" ($meta|ConvertTo-Json -Depth 5)
  & 'D:\DLSSNR-Lab\compile_fit_shaders.exe' $assets
  if($LASTEXITCODE){throw 'Staged shader compile validation failed'}
  if(Test-Path "$assets\shader-cache"){Remove-Item "$assets\shader-cache" -Recurse -Force}
  if(Test-Path "$stage\DLSS5-AMD\logs"){Get-ChildItem "$stage\DLSS5-AMD\logs" -File|Where-Object{$_.Name -notin '.keep','README.txt'}|Remove-Item -Force}
  if(@(Get-ChildItem $assets -Filter '*.f16').Count -lt 50){throw 'Full model assets missing'}
  $files=@(Get-ChildItem $stage -Recurse -File|Where-Object{$_.FullName -ne "$stage\SHA256SUMS.txt"}|Sort-Object FullName)
  $sums=@($files|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLower()+'  '+$_.FullName.Substring($stage.Length+1).Replace('\','/')})
  [IO.File]::WriteAllLines("$stage\SHA256SUMS.txt",$sums,$utf8)
  [IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip,[IO.Compression.CompressionLevel]::Optimal,$false)
  VerifyZip $zip $sums
 }
 if((Get-Item $zip).Length -lt 100MB){throw 'Package unexpectedly small; not a complete release'}
 $hash=(Get-FileHash $zip).Hash.ToLower();WriteUtf8 "$zip.sha256" "$hash  $name.zip`n"
 $result=[pscustomobject]@{name=$name;bytes=(Get-Item $zip).Length;sha256=$hash;files=$sums.Count;verified=$true};$results+=$result;$result|ConvertTo-Json -Compress
 WriteUtf8 "$lab\results.json" ($results|ConvertTo-Json)
}

param([string]$Version='0.38',[string]$SourceCommit='',[string]$ConfigDirectory='D:\DLSSNR-Lab\release-038\scripts',[switch]$Resume)
# 0.38: three full packages from the 0.37 baselines, bit-exact to 0.37 (default flags). Payload = add-on and RE9 runtime rebuilt
# from the tagged source commit (results/package-038/checklist.md; the rebuilt host matched the installed Stellar Blade host on 168
# frames + ticket rollover), and the 62 modules (31 per architecture) installed in Stellar Blade / Onimusha, checked against
# HIP-SHA256SUMS. RE9 host aa3761f2 unchanged. New shader native_format_convert.hlsl (colour-format fallback) is added to
# native-game-tiled-assets; the other shaders are unchanged since 0.37. Templates add DLSS5_FORMAT_FALLBACK=1, DLSS5_HOT_RELOAD=1
# (regular/Magpie) and DLSS5_NETWORK_1080_ROWS=1152. Reads the game install, never writes it.
$ErrorActionPreference='Stop'
if(!$SourceCommit){throw 'SourceCommit required'}
$out='D:\給網友打包';$lab='D:\DLSSNR-Lab\release-038';$utf8=New-Object Text.UTF8Encoding($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$final='D:\DLSSNR-Lab\hip-backend\fusion-round3'
$regularSha='bfba6900079677ff231bfbb210958bfbf68f24964ccf52eb52f5be9836f84976'
$hostSha='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2'
$runtimeSha='ade2d404c2f8d2a7e56ca947ef008a91d6afd90b085e68725e3bfefdde6bc7d7'
$inputShaderSha='5be59a4130e66e9f9f4d370843ef080e0783042d1f730b7a06c072421c92c2b6'
$convertSha='35a1973fc558d7a934cc1190c91f026734405935113568c81e4c7b19c0627b90'
$built='D:\DLSSNR-Lab\release-038\hostcheck'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$addonPath="$built\dlss5-amd.addon64";$runtimePath="$built\LmxxfNrRuntime.dll";$convertPath="$lab\native_format_convert.hlsl"
$moduleRoot="$game\DLSS5-AMD\native-game-tiled-assets\HIP";$shaderSrc="$final\shaders"
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
CheckHash $convertPath $convertSha
CheckHash $runtimePath $runtimeSha
CheckHash "$shaderSrc\native_game_rgb_input.hlsl" $inputShaderSha
foreach($n in 'SOURCE-README.txt','HOST-LICENSE.txt','CORE-LICENSE.txt'){if(!(Test-Path "$lab\$n")){Copy-Item "D:\DLSSNR-Lab\release-037\$n" "$lab\$n"}}
if(!(Test-Path "$lab\re9-presr-source.tar.gz")){throw 'regenerated re9-presr-source.tar.gz missing'}
# Module payload: the 62 installed modules, checked one by one against the release manifest (HIP-SHA256SUMS from the checklist).
$expected=@{};foreach($line in Get-Content "$lab\HIP-SHA256SUMS"){$expected[$line.Substring(66)]=$line.Substring(0,64)}
if($expected.Count -ne 62){throw 'Manifest count'}
$changes=@()
foreach($arch in 'gfx1200','gfx1201'){foreach($f in Get-ChildItem "$moduleRoot\$arch" -Filter *.hsaco){
 $rel="$arch/$($f.Name)";$sha=(Get-FileHash $f.FullName).Hash.ToLower()
 if($expected[$rel] -ne $sha){throw "Module not in manifest or hash differs: $rel"}
 $changes+=[pscustomobject]@{source=$f.FullName;target="DLSS5-AMD/native-game-tiled-assets/HIP/$rel";sha256=$sha}
}}
if($changes.Count -ne 62){throw 'Module count'}
WriteUtf8 "$lab\payload.json" ($changes|ConvertTo-Json)
$variants=@(@{kind='magpie';prefix='Magpie-DLSS5-AMD';flags='hip-magpie-flags.txt';base='0.37'},@{kind='optiscaler';prefix='OptiScaler-DLSS5-AMD';flags='hip-game-flags.txt';base='0.37'},@{kind='re9';prefix='OptiScaler-REFramework-DLSS5-AMD';flags='re9-presr.ini';base='0.37'})
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
  foreach($arch in 'gfx1200','gfx1201'){if(@(Get-ChildItem "$assets\HIP\$arch\*.hsaco").Count -ne 31){throw 'Architecture module count'}}
  if(@(Get-ChildItem "$assets\HIP" -Recurse -Filter *.hsaco).Count -ne 62){throw 'Dual architecture count'}
  # Shader sources: every shipped .hlsl/.hlsli is refreshed from the final tree (flat in the package, dx12-network\ in the tree).
  foreach($f in Get-ChildItem $assets -File|Where-Object{$_.Extension -in '.hlsl','.hlsli'}){
   $src=Join-Path $shaderSrc $f.Name;if(!(Test-Path $src)){$src=Join-Path "$shaderSrc\dx12-network" $f.Name}
   if(!(Test-Path $src)){throw "No final source for shipped shader $($f.Name)"}
   Copy-Item $src $f.FullName -Force
  }
  CheckHash "$assets\native_game_rgb_input.hlsl" $inputShaderSha
  # 0.38: new colour-format fallback shader (the loop above only refreshes shaders already in the baseline package).
  if(Test-Path "$assets\native_format_convert.hlsl"){throw 'baseline already has native_format_convert.hlsl'}
  Copy-Item $convertPath "$assets\native_format_convert.hlsl";CheckHash "$assets\native_format_convert.hlsl" $convertSha
  if($v.kind -ne 're9'){
   Copy-Item $addonPath "$stage\dlss5-amd.addon64" -Force;CheckHash "$stage\dlss5-amd.addon64" $regularSha
   $flags="$stage\DLSS5-AMD\native-game-flags.txt"
   Copy-Item "$ConfigDirectory\$($v.flags)" $flags -Force
   CheckHash $flags (Get-FileHash "$ConfigDirectory\$($v.flags)").Hash
   foreach($f in 'DLSS5_FIT_LARGE=1','DLSS5_HIP_PDL=1','DLSS5_HIP_WAVE_OWNED=1','DLSS5_HIP_C512_M32=1','DLSS5_HIP_VIT_PROJ_N64=1','DLSS5_NETWORK_HEIGHT=auto','DLSS5_HIP_VIT_STREAM=3','DLSS5_DIRECT_IO=1','DLSS5_FRAME_STATS=0','DLSS5_MAKE_RESIDENT_EVERY=60','DLSS5_HIP_SWIN_RUN=1','DLSS5_FORMAT_FALLBACK=1','DLSS5_HOT_RELOAD=1','DLSS5_NETWORK_1080_ROWS=1152'){if(!(HasLine $flags $f)){throw "flags missing $f"}}
   if($v.kind -eq 'optiscaler'){
    foreach($f in 'DLSS5_PRE_UPSCALE_ASYNC=auto','DLSS5_STRENGTH=auto','DLSS5_VIT_ADAPTIVE=1'){if(!(HasLine $flags $f)){throw "flags missing $f"}}
    # regular package: games that ship their own FSR dll (Cyberpunk 2077) need OptiScaler to leave the FFX inputs to the game dll; a no-op for Stellar Blade
    $ini=[IO.File]::ReadAllText("$stage\OptiScaler.ini");$section=''
    foreach($line in Get-Content "$ConfigDirectory\optiscaler-regular.ini"){if($line -match '^\[(.+)\]'){$section=$matches[1]}elseif($line -match '^([^;#][^=]*)=(.*)$'){$ini=SetIni $ini $section $matches[1] $matches[2]}}
    WriteUtf8 "$stage\OptiScaler.ini" $ini
    if(!(Select-String -Path "$stage\OptiScaler.ini" -Pattern '^EnableFfxInputs=false' -Quiet)){throw 'OptiScaler.ini missing EnableFfxInputs=false'}
   }else{
    if(!(HasLine $flags 'DLSS5_VIT_ADAPTIVE=0')){throw 'magpie flags missing DLSS5_VIT_ADAPTIVE=0'}
   }
   # Regular and Magpie packages both load the add-on through ReShade: ship ReShade.ini with the "press Home" tutorial dismissed (ReShade fills the other defaults).
   $rs="$stage\ReShade.ini";$rsText=if(Test-Path $rs){[IO.File]::ReadAllText($rs)}else{''}
   WriteUtf8 $rs (SetIni $rsText 'OVERLAY' 'TutorialProgress' '4')
   if(!(HasLine $rs 'TutorialProgress=4')){throw 'ReShade.ini missing TutorialProgress=4'}
  }else{
   foreach($n in 're9-present.addon64','dlss5-amd.addon64','ReShade64.dll','ReShade.ini','ReShadePreset.ini','DLSS5-AMD\re9-present-mode.txt'){if(Test-Path "$stage\$n"){Remove-Item "$stage\$n" -Force}}
   CheckHash "$stage\dxgi.dll" $hostSha
   Copy-Item $runtimePath "$stage\LmxxfNrRuntime.dll" -Force;CheckHash "$stage\LmxxfNrRuntime.dll" $runtimeSha
   # The runtime reads DLSS5-AMD\native-game-flags.txt (found by walking up from the assets directory).
   $flags="$stage\DLSS5-AMD\native-game-flags.txt"
   Copy-Item "$ConfigDirectory\hip-re9-flags.txt" $flags -Force
   foreach($f in 'DLSS5_FIT_LARGE=1','DLSS5_HIP_WAVE_OWNED=1','DLSS5_HIP_C512_M32=1','DLSS5_HIP_VIT_PROJ_N64=1','DLSS5_NETWORK_HEIGHT=auto','DLSS5_HIP_VIT_STREAM=3','DLSS5_FRAME_STATS=0','DLSS5_VIT_ADAPTIVE=0','DLSS5_HIP_SWIN_RUN=1','DLSS5_FORMAT_FALLBACK=1','DLSS5_NETWORK_1080_ROWS=1152'){if(!(HasLine $flags $f)){throw "re9 flags missing $f"}}
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
  $meta=[ordered]@{version=$Version;package=$name;kind=$v.kind;baseline=$baseline;baseline_sha256=$baselineSha;configuration=$v.flags;modules=62;source_commit=$SourceCommit;regular_addon_sha256=$(if($v.kind -ne 're9'){$regularSha}else{$null});host_sha256=$(if($v.kind -eq 're9'){$hostSha}else{$null});runtime_sha256=$(if($v.kind -eq 're9'){$runtimeSha}else{$null});input_shader_sha256=$inputShaderSha;gpu_smoke=$(if($v.kind -eq 're9'){$gpuSmoke}else{$null});fit_large=$true;bit_exact_vs_previous=$true;note='bit-exact to 0.37 with default flags (float FMA baseline); DLSS5_NETWORK_1080_ROWS=1088 is an opt-in lossy geometry'}
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

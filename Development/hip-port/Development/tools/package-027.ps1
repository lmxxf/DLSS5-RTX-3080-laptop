param([string]$ConfigDirectory=(Join-Path $PSScriptRoot '..\..\scripts'),[switch]$Resume)
$ErrorActionPreference='Stop';$out='D:\給網友打包';$r=$PSScriptRoot;$utf8=New-Object Text.UTF8Encoding($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$regular='d124fa864ecb6a572c5f33a2bb66f698c8922045529d2e0961d7235679da47d5';$re='f2fb57936f6aa95cd90a4c58cc2e80729e5c13e69c2484b743e01f6a803905fa'
$variants=@(
 @{name='Magpie-DLSS5-AMD-0.27';base="$out\history\Magpie-DLSS5-AMD-0.26";flags='hip-magpie-flags.txt';dll='dlss5-amd.addon64';input='release027.addon64';sha=$regular},
 @{name='OptiScaler-DLSS5-AMD-0.27';base="$out\history\OptiScaler-DLSS5-AMD-0.26";flags='hip-game-flags.txt';dll='dlss5-amd.addon64';input='release027.addon64';sha=$regular},
 @{name='OptiScaler-REFramework-DLSS5-AMD-0.27';base="$out\OptiScaler-REFramework-DLSS5-AMD-0.26.1";flags='hip-re9-flags.txt';dll='re9-present.addon64';input='release027-reframework.addon64';sha=$re}
)
foreach($v in $variants){if(!$Resume -and ((Test-Path "$out\$($v.name)") -or (Test-Path "$out\$($v.name).zip"))){throw "Output exists $($v.name)"};if((Get-FileHash "$r\$($v.input)").Hash -ne $v.sha){throw 'Addon hash'};if(!(Test-Path "$ConfigDirectory\$($v.flags)")){throw 'Missing tracked configuration'}}
$modules='D:\DLSSNR-Lab\c256-frag-production-modules';$deep='D:\DLSSNR-Lab\main-reuse-build'
foreach($arch in 'gfx1200','gfx1201'){if(@(Get-ChildItem "$modules\$arch\*.hsaco").Count -ne 24){throw 'Incomplete modules'};$expected=if($arch -eq 'gfx1200'){'7eee02c1a53594387e187bdb74b1113b5fcbd7b756119e7517fc69c6ea928374'}else{'9fdd8a0207a3097d5df7c6bf9ae9298a905e9039c5944030d072c9f9a96eb231'};if((Get-FileHash "$deep\$arch\deep_fast-packed.hsaco").Hash -ne $expected){throw 'Deep module mismatch'}}
$results=@()
foreach($v in $variants){
 $stage="$out\$($v.name)";$zip="$stage.zip"
 if($Resume -and (Test-Path $zip) -and (Test-Path "$stage\SHA256SUMS.txt")){
  $sums=@(Get-Content "$stage\SHA256SUMS.txt");$files=@($sums)
 $z=[IO.Compression.ZipFile]::OpenRead($zip)
 try{$entries=@{};foreach($e in $z.Entries){$entries[$e.FullName.Replace('\','/')]=$e};foreach($line in $sums){$entry=$entries[$line.Substring(66)];if(!$entry){throw 'ZIP missing entry'};$stream=$entry.Open();$h=[Security.Cryptography.SHA256]::Create();try{$actual=([BitConverter]::ToString($h.ComputeHash($stream))).Replace('-','')}finally{$stream.Dispose();$h.Dispose()};if($actual -ne $line.Substring(0,64)){throw 'ZIP hash mismatch'}};if($z.Entries.Count -ne $files.Count+1){throw 'Unexpected ZIP entries'}}finally{$z.Dispose()}
 $hash=(Get-FileHash $zip).Hash.ToLowerInvariant();[IO.File]::WriteAllText("$zip.sha256",$hash+'  '+$v.name+".zip`n",$utf8)
 $result=[pscustomobject]@{name=$v.name;bytes=(Get-Item $zip).Length;sha256=$hash;files=$files.Count;verified=$true};$results+=$result;$result|ConvertTo-Json -Compress
 $results|ConvertTo-Json|Set-Content "$r\results.json" -Encoding UTF8
 continue
 }
 $base=$v.base
 if($v.dll -ne 're9-present.addon64'){
  $archive="$base.zip";$expectedArchive=(Get-Content "$archive.sha256" -Raw).Substring(0,64)
  if((Get-FileHash $archive).Hash -ne $expectedArchive){throw 'Baseline ZIP checksum mismatch'}
  $extract=Join-Path $r ('baseline-'+$v.name)
  if(Test-Path $extract){throw 'Baseline extraction already exists'}
  [IO.Compression.ZipFile]::ExtractToDirectory($archive,$extract)
  $base=Join-Path $extract (Split-Path $base -Leaf)
 }
 $stage="$out\$($v.name)";$zip="$stage.zip"
 foreach($line in Get-Content "$base\SHA256SUMS.txt"){if($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$'){throw 'Bad baseline manifest'};$expectedHash=$matches[1];$relativeName=$matches[2];if((Get-FileHash (Join-Path $base $relativeName)).Hash -ne $expectedHash){throw "Baseline changed $base / $relativeName"}}
 Write-Output "BASE VERIFIED $($v.name)"
 Copy-Item $base $stage -Recurse
 Copy-Item "$r\$($v.input)" "$stage\$($v.dll)" -Force
 Copy-Item "$ConfigDirectory\$($v.flags)" "$stage\DLSS5-AMD\native-game-flags.txt" -Force
 $assets="$stage\DLSS5-AMD\native-game-tiled-assets"
 foreach($arch in 'gfx1200','gfx1201'){
  Copy-Item "$modules\$arch\*.hsaco" "$assets\HIP\$arch" -Force
  Copy-Item "$deep\$arch\deep_fast-packed.hsaco" "$assets\HIP\$arch" -Force
  foreach($m in Get-ChildItem "$assets\HIP\$arch\*.hsaco"){$src=if($m.Name -eq 'deep_fast-packed.hsaco'){"$deep\$arch\$($m.Name)"}else{"$modules\$arch\$($m.Name)"};if((Get-FileHash $m.FullName).Hash -ne (Get-FileHash $src).Hash){throw 'Staged module mismatch'}}
 }
 if(@(Get-ChildItem "$assets\HIP" -Recurse -Filter *.hsaco).Count -ne 48){throw 'Wrong module count'}
 if((Get-FileHash "$stage\DLSS5-AMD\native-game-flags.txt").Hash -ne (Get-FileHash "$ConfigDirectory\$($v.flags)").Hash){throw 'Configuration copy mismatch'}
 $notice=@'
0.27 更新（2026-09-20）
- ViT注意力改为精确流式计算，减少中间存储和重复读取，保持原计算/舍入。
- 新增可选R3跨帧自适应复用，静止输入延长缓存、合并缓存提交；它是有损功能，默认关闭。
- 如需试玩复用，在DLSS5-AMD/native-game-flags.txt设置DLSS5_VIT_ADAPTIVE=1、DLSS5_VIT_REUSE_HOTKEY=1、DLSS5_HIP_GRAPH=0、DLSS5_HIP_VIT_BYTE_STREAM=0。F8切完整/复用；gain从模型自动计算。
- 不包含INT4、2:4剪枝或近似K/V合并；保留原有跳层默认值。
- 配置来自仓库模板，包含完整模型、运行组件及gfx1200/gfx1201内核。不是补丁包。

'@
 if($v.dll -eq 're9-present.addon64'){$notice+="特殊后置版本：RE9与Xbox版《鬼武者》已在0.26.1实玩；0.27更新共用HIP核心。仍固定900P模型、最高1080P SDR输出，上游超分可用。F6开关处理、F7信息层，F8复用切换需显式开启。不代表所有RE引擎游戏兼容。`r`n`r`n"}
 $old=Get-Content "$stage\README.txt" -Raw -Encoding UTF8;$old=$old -replace 'Magpie-DLSS5-AMD-0.26.zip','Magpie-DLSS5-AMD-0.27.zip'
 [IO.File]::WriteAllText("$stage\README.txt",($v.name+"`r`n`r`n"+$notice+"原版使用说明（下方旧版本更新记录保留）：`r`n"+$old),$utf8)
 [IO.File]::WriteAllText("$stage\DLSS5-AMD-VERSION.txt",($v.name+"`naddon_sha256="+$v.sha+"`n"),$utf8)
 $meta=[ordered]@{version='0.27';package=$v.name;addon_sha256=$v.sha;configuration=$v.flags;configuration_sha256=(Get-FileHash "$ConfigDirectory\$($v.flags)").Hash;modules=48;adaptive_default=0;base=$base}
 $meta|ConvertTo-Json|Set-Content "$stage\release.json" -Encoding UTF8
 & 'D:\DLSSNR-Lab\compile_fit_shaders.exe' $assets
 if($LASTEXITCODE){throw 'Shader validation failed'}
 if(Test-Path "$assets\shader-cache"){Remove-Item "$assets\shader-cache" -Recurse -Force}
 Get-ChildItem "$stage\DLSS5-AMD\logs" -File -ErrorAction SilentlyContinue|Where-Object{$_.Name -notin '.keep','README.txt'}|Remove-Item -Force
 $files=@(Get-ChildItem $stage -Recurse -File|Where-Object{$_.FullName -ne "$stage\SHA256SUMS.txt"}|Sort-Object FullName)
 $sums=@($files|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLowerInvariant()+'  '+$_.FullName.Substring($stage.Length+1).Replace('\','/')});[IO.File]::WriteAllLines("$stage\SHA256SUMS.txt",$sums,$utf8)
 [IO.Compression.ZipFile]::CreateFromDirectory($stage,$zip,[IO.Compression.CompressionLevel]::Optimal,$false)
 $z=[IO.Compression.ZipFile]::OpenRead($zip)
 try{$entries=@{};foreach($e in $z.Entries){$entries[$e.FullName.Replace('\','/')]=$e};foreach($line in $sums){$entry=$entries[$line.Substring(66)];if(!$entry){throw 'ZIP missing entry'};$stream=$entry.Open();$h=[Security.Cryptography.SHA256]::Create();try{$actual=([BitConverter]::ToString($h.ComputeHash($stream))).Replace('-','')}finally{$stream.Dispose();$h.Dispose()};if($actual -ne $line.Substring(0,64)){throw 'ZIP hash mismatch'}};if($z.Entries.Count -ne $files.Count+1){throw 'Unexpected ZIP entries'}}finally{$z.Dispose()}
 $hash=(Get-FileHash $zip).Hash.ToLowerInvariant();[IO.File]::WriteAllText("$zip.sha256",$hash+'  '+$v.name+".zip`n",$utf8)
 $result=[pscustomobject]@{name=$v.name;bytes=(Get-Item $zip).Length;sha256=$hash;files=$files.Count;verified=$true};$results+=$result;$result|ConvertTo-Json -Compress
 $results|ConvertTo-Json|Set-Content "$r\results.json" -Encoding UTF8
}

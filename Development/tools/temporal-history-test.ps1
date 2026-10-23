param([Parameter(Mandatory=$true)][ValidateSet('off','on','restore')][string]$Mode,[string]$PackageRoot=$PSScriptRoot,[string]$BackupReceipt='')
# Player-run 0.41-a trial switch. Never hot-switch. The first backup survives off/on/off.
$ErrorActionPreference='Stop'
$PackageRoot=[IO.Path]::GetFullPath($PackageRoot);$lab=Join-Path $PackageRoot 'DLSS5-AMD'
$version=Join-Path $PackageRoot 'DLSS5-AMD-VERSION.txt'
if(!(Test-Path $version) -or (Get-Content $version -Raw) -notmatch '0\.41-a'){throw 'Run against the extracted regular 0.41-a package (-PackageRoot).'}
if(!(Test-Path "$lab\default-config.txt")){throw 'Missing regular package configuration'}
if(Get-Process SB-Win64-Shipping,re9,OnimushaWotS,LOP-Win64-Shipping,Magpie,SandFall*,Cyberpunk2077,WoLong*,Forza* -ErrorAction SilentlyContinue){throw 'Close the game and Magpie before switching; restart afterwards.'}
$runningHere=@(Get-Process|Where-Object {try{$_.Path -and $_.Path.StartsWith($PackageRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)}catch{$false}})
if($runningHere.Count){throw ('Close processes launched from the package/game directory: '+($runningHere.Name -join ', '))}
$utf8=New-Object Text.UTF8Encoding($false);$backups=Join-Path $lab 'history-test-backups';$active=Join-Path $backups 'active-receipt.txt'
$custom=Join-Path $lab 'custom-config.txt';$native=Join-Path $lab 'native-game-flags.txt';$marker=Join-Path $lab 'temporal-history.txt'
$allowed=@([IO.Path]::GetFullPath($custom),[IO.Path]::GetFullPath($native),[IO.Path]::GetFullPath($marker))
function CheckReceipt($receipt){
 foreach($r in $receipt.files){
  $p=[IO.Path]::GetFullPath($r.path);if($p -notin $allowed){throw 'Receipt points outside the allowed trial files'}
  $present=Test-Path -LiteralPath $p
  if($present -ne [bool]$r.after_present){throw "File presence changed after trial; refusing overwrite: $p"}
  if($present -and (Get-FileHash -LiteralPath $p).Hash -ne $r.after_sha256){throw "File changed after trial; refusing overwrite: $p"}
  if($r.existed){$saved=[IO.Path]::GetFullPath($r.backup)
   if(!$saved.StartsWith($backups+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Backup path outside trial backup directory'}
   if(!(Test-Path -LiteralPath $saved) -or (Get-FileHash -LiteralPath $saved).Hash -ne $r.before_sha256){throw 'Original backup SHA mismatch'}
  }
 }
}
if($Mode -eq 'restore'){
 if(!$BackupReceipt -and (Test-Path $active)){$BackupReceipt=[IO.File]::ReadAllText($active).Trim()}
 if(!$BackupReceipt -or !(Test-Path -LiteralPath $BackupReceipt)){throw 'No active backup; provide -BackupReceipt <first receipt.json>'}
 $receipt=Get-Content -LiteralPath $BackupReceipt -Raw|ConvertFrom-Json;CheckReceipt $receipt
 foreach($r in $receipt.files){if($r.existed){Copy-Item -LiteralPath $r.backup -Destination $r.path -Force}else{if(Test-Path -LiteralPath $r.path){[IO.File]::Delete($r.path)}}}
 if(Test-Path $active){[IO.File]::Delete($active)}
 Write-Output "Restored original configs and legacy marker from $BackupReceipt. Restart the game.";return
}
$settings=[ordered]@{
 DLSS5_TEMPORAL_HISTORY_EXPERIMENT=$(if($Mode -eq 'on'){'1'}else{'0'});DLSS5_TEMPORAL_MV_UNJITTERED='1';
 DLSS5_MULTI_PASS='1';DLSS5_MULTI_PASS_SKIN_PROTECT='0';DLSS5_VIT_ADAPTIVE='0';DLSS5_VIT_REUSE_HOTKEY='0';
 DLSS5_HIP_GRAPH='0';DLSS5_OVERLAP='0';DLSS5_FAST_TEMPORAL='0';DLSS5_HISTORY_GUARD='0';DLSS5_OUTPUT_SMOOTH='0';DLSS5_PRE_UPSCALE='auto'
}
foreach($k in $settings.Keys){foreach($target in 'Process','User','Machine'){
 $v=[Environment]::GetEnvironmentVariable($k,$target)
 if($null -ne $v){throw "Environment override $k=$v ($target) wins over files. Remove it from the launch environment; this script does not edit environment settings."}
}}
if(Test-Path $active){
 $receiptPath=[IO.File]::ReadAllText($active).Trim()
 if(!$receiptPath.StartsWith($backups+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Active receipt path outside package'}
 $receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json;CheckReceipt $receipt
 $original=@($receipt.files)
}else{
 $backup=Join-Path $backups (Get-Date -Format 'yyyyMMdd-HHmmss-ffff');New-Item -ItemType Directory $backup|Out-Null;$receiptPath=Join-Path $backup 'receipt.json'
 $original=@()
 foreach($p in $custom,$native,$marker){
  $exists=Test-Path -LiteralPath $p;$saved=$null;$sha=$null
  if($exists){$saved=Join-Path $backup ([IO.Path]::GetFileName($p));Copy-Item -LiteralPath $p -Destination $saved;$sha=(Get-FileHash -LiteralPath $p).Hash}
  $original+=@([pscustomobject]@{path=$p;existed=$exists;backup=$saved;before_sha256=$sha;touched=($p -eq $custom -or $p -eq $marker -or $exists);after_present=$exists;after_sha256=$sha})
 }
}
# Preflight every file before writing. Rollback uses the immediately preceding state;
# immutable backups remain the first pre-test files across repeated off/on/off calls.
$plans=@()
foreach($r in $original){
 $p=$r.path;$exists=Test-Path -LiteralPath $p;$bytes=$(if($exists){[IO.File]::ReadAllBytes($p)}else{$null})
 if($p -eq $marker){$plans+=@([pscustomobject]@{record=$r;before_present=$exists;before_bytes=$bytes;remove=$true;text='';bom=$false});continue}
 if(!$r.touched){continue}
 $bom=$exists -and $bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191;$text=''
 if($exists){if($bytes.Length -ge 2 -and (($bytes[0] -eq 255 -and $bytes[1] -eq 254) -or ($bytes[0] -eq 254 -and $bytes[1] -eq 255))){throw 'UTF16 config unsupported; no files changed'};$strict=New-Object Text.UTF8Encoding($false,$true);$text=[IO.File]::ReadAllText($p,$strict)}
 $newline=$(if($text.Contains([string][char]13+[char]10)){[string][char]13+[char]10}else{[string][char]10})
 foreach($k in $settings.Keys){$pattern='(?m)^[ \t]*'+[regex]::Escape($k)+'=[^\r\n]*';$value=$k+'='+$settings[$k]
  if([regex]::IsMatch($text,$pattern)){$text=[regex]::Replace($text,$pattern,$value)}else{if($text.Length -and !$text.EndsWith([string][char]10)){$text+=$newline};$text+=$value+$newline}
 }
 $plans+=@([pscustomobject]@{record=$r;before_present=$exists;before_bytes=$bytes;remove=$false;text=$text;bom=$bom})
}
try{
 foreach($p in $plans){
  $path=$p.record.path
  if($p.remove){if(Test-Path -LiteralPath $path){[IO.File]::Delete($path)}}else{
   [IO.File]::WriteAllText($path,$p.text,(New-Object Text.UTF8Encoding($p.bom)))
   foreach($k in $settings.Keys){if(!(Select-String -LiteralPath $path -Pattern ('^'+[regex]::Escape($k)+'='+[regex]::Escape($settings[$k])+'$') -Quiet)){throw "Config readback mismatch $k"}}
  }
 }
 foreach($r in $original){$r.after_present=Test-Path -LiteralPath $r.path;$r.after_sha256=$(if($r.after_present){(Get-FileHash -LiteralPath $r.path).Hash}else{$null})}
 $receipt=[ordered]@{mode=$Mode;settings=$settings;files=$original;note='First backup retained across off/on/off; legacy marker moved for pureSpatial OFF. MV_UNJITTERED is assumed, not detected.'}
 [IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 6),$utf8);[IO.File]::WriteAllText($active,$receiptPath,$utf8)
}catch{
 foreach($p in $plans){if($p.before_present){[IO.File]::WriteAllBytes($p.record.path,$(if($null -ne $p.before_bytes){[byte[]]$p.before_bytes}else{[byte[]]@()}))}else{if(Test-Path -LiteralPath $p.record.path){[IO.File]::Delete($p.record.path)}}};throw
}
Write-Output "Applied $Mode; legacy marker absent for both test modes. Original backup: $receiptPath"
Write-Output 'Restart the game. Startup MP1 is required; F9 from an MP3 startup is insufficient. Check requested/active/reason in the history logs.'

param([ValidateSet('Install','Restore')][string]$Action='Install')
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$lab='D:\DLSSNR-Lab';$backup="$lab\pre-upscale\before-feature-byte"
$source="$lab\hip-backend\mh-ex-production-modules"
$moduleDir='DLSS5-AMD\native-game-tiled-assets\HIP'
$flagsRel='DLSS5-AMD\native-game-flags.txt';$flagsPath=Join-Path $game $flagsRel
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}}
function Restore {
 Closed
 $records=@(Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json)
 foreach($r in $records){if((Get-FileHash (Join-Path "$backup\files" $r.relative)).Hash -ne $r.sha256){throw 'Backup mismatch'}}
 foreach($r in $records){$dst=Join-Path $game $r.relative;Copy-Item (Join-Path "$backup\files" $r.relative) $dst -Force;if((Get-FileHash $dst).Hash -ne $r.sha256){throw 'Restore mismatch'}}
 'RESTORED_FEATURE_BYTE_BASELINE'
}
Closed
if($Action -eq 'Restore'){Restore;exit}
if(Test-Path $backup){throw 'Backup already exists'}
if((Get-FileHash "$game\dlss5-amd.addon64").Hash -ne 'BE9E82CEE99037EF92EB2BEC18ACC51C428EC3CD02CCF80A1FD1033B3A8C3119'){throw 'Unexpected addon; inspect before deployment'}
$expected=@{
 'c32_fused_ffn_attention.hsaco'='0F3AFF3FB906BD493443B1C74440716969B780D39FF98C785412DD36112F042B'
 'c32_fused_ffn_attention-packed.hsaco'='31E295CC7D90CE7F77ACCC7BB517562C8ECBBFF44269A2587298135EB378F7A1'
 'multihead_fused_attention.hsaco'='DEA239E4AAA36825884CA052AEEA045BB1BA368AFA738F728B758A1930C7BA6C'
}
$modules=@(Get-ChildItem $source -Filter *.hsaco)
if($modules.Count -ne 24){throw 'Expected 24 validated modules'}
foreach($m in $modules){
 $hash=(Get-FileHash $m.FullName).Hash
 if($expected.ContainsKey($m.Name)){if($hash -ne $expected[$m.Name]){throw 'Candidate hash mismatch'}}
 elseif($hash -ne (Get-FileHash "$game\$moduleDir\$($m.Name)").Hash){throw 'Other module differs; inspect baseline'}
}
$flags=[IO.File]::ReadAllText($flagsPath)
if($flags -match '(?m)^DLSS5_HIP_MODULES=.+$'){throw 'External module path override; inspect first'}
$settings=Join-Path $env:LOCALAPPDATA 'SB\Saved\Config\WindowsNoEditor\GameUserSettings.ini'
$watch=@($settings,"$game\OptiScaler.ini","$game\dlss5-amd.addon64");$before=@{};foreach($p in $watch){$before[$p]=(Get-FileHash $p).Hash}
$rels=@($expected.Keys|ForEach-Object{"$moduleDir\$_"})+@($flagsRel)
$records=@(foreach($rel in $rels){
 $src=Join-Path $game $rel;$dst=Join-Path "$backup\files" $rel
 New-Item -ItemType Directory -Force (Split-Path $dst)|Out-Null;Copy-Item $src $dst
 $hash=(Get-FileHash $src).Hash;if((Get-FileHash $dst).Hash -ne $hash){throw 'Backup failed'}
 [pscustomobject]@{relative=$rel;sha256=$hash}
})
$records|ConvertTo-Json -Depth 3|Set-Content "$backup\manifest.json"
try{
 Closed
 foreach($name in $expected.Keys){Copy-Item "$source\$name" "$game\$moduleDir\$name" -Force;if((Get-FileHash "$game\$moduleDir\$name").Hash -ne $expected[$name]){throw 'Installed module mismatch'}}
 foreach($kv in @(@('DLSS5_HIP_MH_FEATURE_BYTE','1'),@('DLSS5_HIP_MH_PROJ_DIAG_FB','1'),@('DLSS5_HIP_MH_BYTE_STREAM','0'),@('DLSS5_HIP_VIT_BYTE_STREAM','0'))){
  $pattern='(?m)^'+[regex]::Escape($kv[0])+'=[^\r\n]*';$line=$kv[0]+'='+$kv[1]
  if([regex]::IsMatch($flags,$pattern)){$flags=[regex]::Replace($flags,$pattern,$line)}else{$flags=$flags.TrimEnd()+"`r`n"+$line+"`r`n"}
 }
 [IO.File]::WriteAllText($flagsPath,$flags,(New-Object Text.UTF8Encoding($false)))
 foreach($p in $watch){if((Get-FileHash $p).Hash -ne $before[$p]){throw 'Game settings/addon changed'}}
 'INSTALLED modules=3 flags=local_byte_feature+diag full_byte_streams=off'
 Get-Content $flagsPath|Select-String 'SHOW_FPS|NOTICE|NETWORK_HEIGHT|PRE_UPSCALE|MH_FEATURE_BYTE|MH_PROJ_DIAG_FB|MH_BYTE_STREAM|VIT_BYTE_STREAM'
 "BACKUP=$backup"
}catch{Restore;throw}

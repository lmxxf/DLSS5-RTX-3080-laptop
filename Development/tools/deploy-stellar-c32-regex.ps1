param([ValidateSet('Install','Restore')][string]$Action='Install')
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$lab='D:\DLSSNR-Lab';$backup="$lab\pre-upscale\before-c32-regex"
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game and Magpie before deployment'}}
function Restore {
 Closed
 foreach($r in @(Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json)){
  $src=Join-Path "$backup\files" $r.relative
  if((Get-FileHash $src).Hash -ne $r.sha256){throw 'Backup hash mismatch'}
 }
 foreach($r in @(Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json)){
  Copy-Item (Join-Path "$backup\files" $r.relative) (Join-Path $game $r.relative) -Force
 }
 'RESTORED'
}
Closed
if($Action -eq 'Restore'){Restore;exit}
if(Test-Path $backup){throw 'Deployment backup already exists'}
$items=@(
 @{relative='dlss5-amd.addon64';source="$lab\pre-upscale\native-overlay-flags.addon64";sha='BE9E82CEE99037EF92EB2BEC18ACC51C428EC3CD02CCF80A1FD1033B3A8C3119'},
 @{relative='DLSS5-AMD\native-game-tiled-assets\HIP\c32_fused_ffn_attention.hsaco';source="$lab\hip-backend\c32-regex-production-modules\c32_fused_ffn_attention.hsaco";sha='145D3DD186DB27AB13AE82B17A6690992FD93DE8E97599552C6A454FF42AED1C'},
 @{relative='DLSS5-AMD\native-game-tiled-assets\HIP\c32_fused_ffn_attention-packed.hsaco';source="$lab\hip-backend\c32-regex-production-modules\c32_fused_ffn_attention-packed.hsaco";sha='71BAEDCC0486790C48C884917AB96FAA722F781BF415D195E195928E651921DE'}
)
# Also update existing loader caches, if any, to prevent a stale addon winning.
if(Test-Path "$game\_storage_"){
 foreach($f in Get-ChildItem "$game\_storage_" -Recurse -File -Filter dlss5-amd.addon64){$items+=@{relative=$f.FullName.Substring($game.Length+1);source=$items[0].source;sha=$items[0].sha}}
}
foreach($i in $items){if((Get-FileHash $i.source).Hash -ne $i.sha){throw 'Candidate hash mismatch'};if(!(Test-Path (Join-Path $game $i.relative))){throw 'Expected installed file missing'}}
$flags="$game\DLSS5-AMD\native-game-flags.txt";$flagsHash=(Get-FileHash $flags).Hash
$records=@(foreach($i in $items){
 $src=Join-Path $game $i.relative;$dst=Join-Path "$backup\files" $i.relative
 New-Item -ItemType Directory -Force (Split-Path $dst)|Out-Null
 Copy-Item $src $dst
 $hash=(Get-FileHash $src).Hash
 if((Get-FileHash $dst).Hash -ne $hash){throw 'Backup copy mismatch'}
 [pscustomobject]@{relative=$i.relative;sha256=$hash}
})
$records|ConvertTo-Json -Depth 3|Set-Content "$backup\manifest.json"
Copy-Item $flags "$backup\native-game-flags.txt.snapshot"
try{
 Closed
 foreach($i in $items){$dst=Join-Path $game $i.relative;Copy-Item $i.source $dst -Force;if((Get-FileHash $dst).Hash -ne $i.sha){throw 'Installed hash mismatch'}}
 if((Get-FileHash $flags).Hash -ne $flagsHash){throw 'Flags changed during deployment'}
 "INSTALLED files=$($items.Count) flags_unchanged=1 backup=$backup"
 Get-Content $flags|Select-String 'SHOW_FPS|NOTICE|PRE_UPSCALE|NETWORK_HEIGHT'
}catch{Restore;throw}

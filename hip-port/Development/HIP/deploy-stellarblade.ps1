param(
 [ValidateSet('Deploy','Restore')][string]$Action='Deploy',
 [string]$ExpectedSha=''
)
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$lab='D:\DLSSNR-Lab'
$localRoot=Join-Path $game 'DLSS5-AMD'
$target=Join-Path $game 'native-submission-order.addon64'
$backup=Join-Path $PSScriptRoot 'before-stellarblade'
$candidate=Join-Path $PSScriptRoot 'dlss5-hip-candidate.addon64'
$moduleSource=Join-Path $PSScriptRoot 'modules'
$utf8=New-Object Text.UTF8Encoding($false)
function Assert-Closed {
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Stellar Blade is running. Close the game before deploying/restoring.'}
}
function Disable-LocalRoot {
 if(Test-Path $localRoot){
  # Rename on the same volume; never recurse through the asset junction.
  $disabled='DLSS5-AMD.HIP-disabled-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')
  Rename-Item -LiteralPath $localRoot -NewName $disabled
  Write-Output "Disabled HIP data: $disabled"
 }
}
function Restore-Original {
 Assert-Closed
 $record=Get-Content (Join-Path $backup 'backup.json') -Raw | ConvertFrom-Json
 $saved=Join-Path $backup 'native-submission-order.addon64'
 if((Get-FileHash $saved).Hash -ne $record.original_sha256){throw 'Original DLL backup hash mismatch.'}
 Copy-Item $saved $target -Force
 if((Get-FileHash $target).Hash -ne $record.original_sha256){throw 'Restored DLL verification failed.'}
 Disable-LocalRoot
 Write-Output "Restored 900P HLSL DLL: $($record.original_sha256)"
}
Assert-Closed
if($Action -eq 'Restore'){
 if((Test-Path $localRoot) -and !(Test-Path (Join-Path $localRoot 'HIP-CANDIDATE.txt'))){throw 'Unrecognized local data directory; refusing to rename it.'}
 Restore-Original;exit 0
}
if(Test-Path $localRoot){throw 'Existing game-local DLSS5-AMD directory requires inspection.'}
if(Test-Path $backup){throw 'Backup already exists; do not overwrite the rollback copy.'}
if(!$ExpectedSha -or (Get-FileHash $candidate).Hash -ne $ExpectedSha){throw 'Candidate DLL hash mismatch.'}
if(!(Test-Path 'C:\Windows\System32\amdhip64_7.dll')){throw 'HIP7 runtime missing.'}
foreach($file in @('d3d12.dll','amd_fidelityfx_dx12.dll','native-submission-order.addon64')){if(!(Test-Path (Join-Path $game $file))){throw "Game dependency missing: $file"}}
$sourceAssets=Join-Path $lab 'network-720p\DLSS5-AMD\native-game-tiled-assets'
if(!(Test-Path (Join-Path $sourceAssets 'noise.f32'))){throw 'Existing game assets missing.'}
$moduleManifest=Get-Content (Join-Path $moduleSource 'deployment-modules.json') -Raw | ConvertFrom-Json
if($moduleManifest.Count -ne 24){throw 'Expected complete 24-module candidate set.'}
foreach($m in $moduleManifest){if((Get-FileHash (Join-Path $moduleSource $m.name)).Hash -ne $m.sha256){throw "Staged module mismatch: $($m.name)"}}
New-Item -ItemType Directory $backup | Out-Null
Copy-Item $target (Join-Path $backup 'native-submission-order.addon64')
Copy-Item (Join-Path $lab 'native-game-flags.txt') (Join-Path $backup 'global-flags-reference.txt')
$originalHash=(Get-FileHash $target).Hash
[IO.File]::WriteAllText((Join-Path $backup 'backup.json'),([pscustomobject]@{original_sha256=$originalHash;candidate_sha256=$ExpectedSha;game=$game;created=(Get-Date -Format o)}|ConvertTo-Json),$utf8)
$created=$false
try{
 Assert-Closed
 New-Item -ItemType Directory $localRoot | Out-Null;$created=$true
 foreach($name in @('logs','HIP')){New-Item -ItemType Directory (Join-Path $localRoot $name) | Out-Null}
 New-Item -ItemType Junction -Path (Join-Path $localRoot 'native-game-tiled-assets') -Value $sourceAssets | Out-Null
 foreach($m in $moduleManifest){Copy-Item (Join-Path $moduleSource $m.name) (Join-Path $localRoot ('HIP\'+$m.name))}
 Copy-Item (Join-Path $moduleSource 'deployment-modules.json') (Join-Path $localRoot 'HIP\deployment-modules.json')
 $flags=@(Get-Content (Join-Path $lab 'native-game-flags.txt') | Where-Object {$_ -notmatch '^DLSS5_HIP_(FAST|MODULES)=' -and $_ -notmatch '^DLSS5_TEST_ASYNC_SUBMIT='})
 # Live HIP/D3D12 deferred submissions corrupt the menu image after the first
 # frame. Keep CPU fence waits until the cross-API ordering issue is resolved.
 $flags+='DLSS5_TEST_ASYNC_SUBMIT=0'
 $flags+='DLSS5_HIP_FAST=1';$flags+='DLSS5_HIP_MODULES='+(Join-Path $localRoot 'HIP')
 [IO.File]::WriteAllText((Join-Path $localRoot 'native-game-flags.txt'),($flags -join "`n")+"`n",$utf8)
 foreach($marker in @('continuous-every-frame.txt','temporal-history.txt')){[IO.File]::WriteAllText((Join-Path $localRoot $marker),"1`n",$utf8)}
 [IO.File]::WriteAllText((Join-Path $localRoot 'HIP-CANDIDATE.txt'),"HIP7 / fast900P / packed weights`nDLL SHA256=$ExpectedSha`nRollback: $PSScriptRoot\restore-stellarblade.cmd`n",$utf8)
 Assert-Closed
 Copy-Item $candidate $target -Force
 if((Get-FileHash $target).Hash -ne $ExpectedSha){throw 'Installed DLL hash mismatch.'}
 foreach($m in $moduleManifest){if((Get-FileHash (Join-Path $localRoot ('HIP\'+$m.name))).Hash -ne $m.sha256){throw "Installed module mismatch: $($m.name)"}}
 Write-Output "INSTALLED=$target";Write-Output "DLL_SHA256=$ExpectedSha";Write-Output "MODULES=$($moduleManifest.Count)";Write-Output "BACKUP=$backup";Write-Output 'MODE=HIP7 fast900P packed weights, native temporal, game-local configuration'
}catch{
 if($created){Restore-Original}
 throw
}

param([ValidateSet('Install','Restore')][string]$Action='Install',
 [string]$Candidate='D:\DLSSNR-Lab\pre-upscale\native-f6-passthrough.addon64',
 [string]$ExpectedSha='B8E357411C925E7DC2A4EF6E2AFBF64CD23E730A8CFD2C958DFA3FFED1460CBD')
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$backup='D:\DLSSNR-Lab\pre-upscale\before-f6-passthrough'
function Closed {if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Exit Stellar Blade before replacing its addon.'}}
Closed
if($Action -eq 'Restore'){
 $records=@(Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json)
 foreach($r in $records){if((Get-FileHash (Join-Path $backup $r.relative)).Hash -ne $r.sha256){throw 'Backup hash mismatch'}}
 foreach($r in $records){Copy-Item (Join-Path $backup $r.relative) (Join-Path $game $r.relative) -Force}
 'RESTORED_F6_PREVIOUS_ADDON';exit
}
if(Test-Path $backup){throw 'Backup already exists; inspect before repeating installation'}
if((Get-FileHash $Candidate).Hash -ne $ExpectedSha){throw 'Candidate hash mismatch'}
$targets=@(Get-Item "$game\dlss5-amd.addon64")
if(Test-Path "$game\_storage_"){$targets+=@(Get-ChildItem "$game\_storage_" -Recurse -File -Filter dlss5-amd.addon64)}
New-Item -ItemType Directory $backup|Out-Null
$records=@(foreach($target in $targets){
 $relative=$target.FullName.Substring($game.Length+1);$saved=Join-Path $backup $relative
 New-Item -ItemType Directory -Force (Split-Path $saved)|Out-Null
 Copy-Item $target.FullName $saved
 $sha=(Get-FileHash $target.FullName).Hash
 if((Get-FileHash $saved).Hash -ne $sha){throw 'Backup verification failed'}
 [pscustomobject]@{relative=$relative;sha256=$sha}
})
$records|ConvertTo-Json -Depth 3|Set-Content "$backup\manifest.json"
try{
 Closed
 foreach($target in $targets){Copy-Item $Candidate $target.FullName -Force;if((Get-FileHash $target.FullName).Hash -ne $ExpectedSha){throw 'Installed hash mismatch'}}
 "INSTALLED_SHA=$ExpectedSha FILES=$($targets.Count) BACKUP=$backup"
}catch{
 Closed
 foreach($r in $records){Copy-Item (Join-Path $backup $r.relative) (Join-Path $game $r.relative) -Force}
 throw
}

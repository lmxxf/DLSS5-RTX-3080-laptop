param([switch]$Restore,
 [ValidateSet(0,1)][int]$AsyncSubmit=0,
 [string]$BackupName='before-c32-vit-blocked',
 [string]$CandidateName='native-c32-vit-blocked.addon64',
 [string]$ModulesName='vit-contract-modules',
 [string]$ExpectedSha='4C0620A559A6A1CA6D633F5DCFB8B3B241D2A56116B7BEE714917256859278F0')
$ErrorActionPreference='Stop'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
$root=Join-Path $game 'DLSS5-AMD'
$lab='D:\DLSSNR-Lab\hip-backend'
$backup=Join-Path (Join-Path $lab 'stellarblade-hip') $BackupName
$candidate=Join-Path (Join-Path $lab 'stellarblade-hip') $CandidateName
$modules=Join-Path $lab $ModulesName
$target=Join-Path $game 'native-submission-order.addon64'
$expected=$ExpectedSha
function Closed {if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Close Stellar Blade before replacing DLL/modules.'}}
function RestoreBackup {
 Closed
 $record=Get-Content "$backup\manifest.json" -Raw|ConvertFrom-Json
 if((Get-FileHash "$backup\native-submission-order.addon64").Hash -ne $record.dll){throw 'Backup DLL hash mismatch'}
 foreach($m in $record.modules){if((Get-FileHash "$backup\HIP\$($m.name)").Hash -ne $m.sha256){throw 'Backup module hash mismatch'}}
 Copy-Item "$backup\native-submission-order.addon64" $target -Force
 Copy-Item "$backup\HIP\*" "$root\HIP" -Force
 Copy-Item "$backup\native-game-flags.txt" "$root\native-game-flags.txt" -Force
 if(Test-Path "$backup\HIP-CANDIDATE.txt"){Copy-Item "$backup\HIP-CANDIDATE.txt" "$root\HIP-CANDIDATE.txt" -Force}
 Write-Output 'Restored previous HIP DLL/modules/configuration.'
}
Closed
if($Restore){RestoreBackup;exit}
if(Test-Path $backup){throw 'Backup exists; inspect before repeating deployment'}
if((Get-FileHash $candidate).Hash -ne $expected){throw 'Candidate DLL mismatch'}
$files=@(Get-ChildItem $modules -Filter '*.hsaco')
if($files.Count -ne 24){throw 'Expected 24 modules'}
$manifest=@($files|ForEach-Object{[pscustomobject]@{name=$_.Name;sha256=(Get-FileHash $_.FullName).Hash}})
if(!(Test-Path "$root\HIP-CANDIDATE.txt")){throw 'Existing HIP install not recognized'}
New-Item -ItemType Directory $backup|Out-Null
Copy-Item $target "$backup\native-submission-order.addon64"
Copy-Item "$root\HIP" "$backup\HIP" -Recurse
Copy-Item "$root\native-game-flags.txt" "$backup\native-game-flags.txt"
Copy-Item "$root\HIP-CANDIDATE.txt" "$backup\HIP-CANDIDATE.txt"
$old=@(Get-ChildItem "$backup\HIP" -Filter '*.hsaco'|ForEach-Object{[pscustomobject]@{name=$_.Name;sha256=(Get-FileHash $_.FullName).Hash}})
[pscustomobject]@{dll=(Get-FileHash $target).Hash;modules=$old}|ConvertTo-Json -Depth 4|Set-Content "$backup\manifest.json"
try {
 Closed
 foreach($m in $manifest){Copy-Item "$modules\$($m.name)" "$root\HIP\$($m.name)" -Force}
 Copy-Item $candidate $target -Force
 foreach($m in $manifest){if((Get-FileHash "$root\HIP\$($m.name)").Hash -ne $m.sha256){throw 'Installed module mismatch'}}
 if((Get-FileHash $target).Hash -ne $expected){throw 'Installed DLL mismatch'}
 $utf8=New-Object Text.UTF8Encoding($false)
 $flags=@(Get-Content "$root\native-game-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_TEST_ASYNC_SUBMIT='})
 $flags+="DLSS5_TEST_ASYNC_SUBMIT=$AsyncSubmit"
 [IO.File]::WriteAllText("$root\native-game-flags.txt",($flags -join "`n")+"`n",$utf8)
 foreach($name in @('continuous-every-frame.txt','temporal-history.txt')){[IO.File]::WriteAllText("$root\$name","1`n",$utf8)}
 $manifest|ConvertTo-Json -Depth 3|Set-Content "$root\HIP\deployment-modules.json"
 [IO.File]::WriteAllText("$root\HIP-CANDIDATE.txt","HIP7 fast900P / mapped C32 / fused MH FFN / blocked ViT`nDLL SHA256=$expected`nASYNC_SUBMIT=$AsyncSubmit`n",$utf8)
 Write-Output "INSTALLED_SHA=$expected MODULES=$($files.Count) BACKUP=$backup"
}catch{RestoreBackup;throw}

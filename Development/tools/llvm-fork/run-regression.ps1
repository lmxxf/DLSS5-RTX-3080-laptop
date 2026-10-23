$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929'
function Idle {
 if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
}
Idle
$snap=Get-Content "$root\snapshot.json" -Raw|ConvertFrom-Json
foreach($f in $snap.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed baseline changed: $($f.path)"}}
Expand-Archive -Path "$root\candidate.zip" -DestinationPath "$root\candidate" -Force
$manifest=Get-Content "$root\candidate\manifest.json" -Raw|ConvertFrom-Json
if(@($manifest.modules).Count -ne 60){throw 'Incomplete candidate manifest'}
foreach($m in $manifest.modules){if((Get-FileHash "$root\candidate\$($m.target)\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Candidate transfer hash mismatch'}}
foreach($tag in 'A','L'){
 New-Item -ItemType Directory -Force "$root\flat-$tag"|Out-Null
}
Copy-Item "$root\baseline\gfx1201\*.hsaco" "$root\flat-A" -Force
Copy-Item "$root\candidate\gfx1201\*.hsaco" "$root\flat-L" -Force
Copy-Item 'D:\DLSSNR-Lab\hip-backend\kernel-map\benchmark-production.exe' "$root\benchmark-production.exe" -Force
Get-FileHash "$root\benchmark-production.exe"|Format-List
foreach($mode in 0,1){
 Idle
 $batch=if($mode){'adaptive'}else{'correct'}
 & "$root\regression.ps1" -Set L -Adaptive $mode -BenchName benchmark-production.exe -CandidateBenchName benchmark-production.exe -CorrectnessOnly -Batch $batch *> "$root\regression-$batch.log"
 if(!$?){throw "Replay failed: $batch"}
}
$hashes=@()
foreach($batch in 'correct','adaptive'){
 $d="$root\runtime-regression-L-$batch"
 foreach($slot in Get-ChildItem $d -Directory){
  foreach($f in Get-ChildItem $slot.FullName -Filter '*frame-*.f16'){
   if($f.Name -match 'frame-(\d+)'){$hashes += [pscustomobject]@{batch="runtime-regression-L-$batch";slot=$slot.Name;frame=$f.Name;sha=(Get-FileHash $f.FullName).Hash}}
  }
 }
}
$hashes|Export-Csv "$root\hashes.csv" -NoTypeInformation
foreach($f in $snap.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed files changed: $($f.path)"}}
Write-Output 'Replay finished; compare hashes and adaptive decisions before accepting.'

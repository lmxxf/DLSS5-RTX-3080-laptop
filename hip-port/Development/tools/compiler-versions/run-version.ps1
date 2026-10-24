param([ValidateSet('L20','L21','L22')][string]$Version,
      [ValidateSet('Regression','Timing','Collect')][string]$Action='Regression')
$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
function Idle {
 if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile|^recorder|^microbench|^runtime-smoke'}){throw 'GPU lab busy'}
}
function Check {
 Idle
 $prepared=Get-Content "$root\prepared.json" -Raw|ConvertFrom-Json
 if((Get-FileHash "$root\benchmark-production.exe").Hash -ne $prepared.host){throw 'Replay host changed'}
 $snapshot=Get-Content "$root\snapshot.json" -Raw|ConvertFrom-Json
 foreach($f in $snapshot.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed baseline changed: $($f.path)"}}
 if(!(Test-Path "$root\driver-identity-pass.json")){throw 'Driver rebuild identity not verified'}
 $modules=Get-Content "$root\manifest-$Version.json" -Raw|ConvertFrom-Json
 foreach($m in $modules.modules|Where-Object{$_.target -eq 'gfx1201'}){
  if((Get-FileHash "$root\flat-$Version\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Candidate changed'}
 }
 $driver=Get-Content "$root\driver\gfx1201\modules.json" -Raw|ConvertFrom-Json
 foreach($m in $driver){if((Get-FileHash "$root\flat-A\$($m.module).hsaco").Hash -ne $m.sha256){throw 'Driver set changed'}}
}
if($Action -eq 'Regression'){
 Check
 foreach($adaptive in 0,1){
  $batch=if($adaptive){'adaptive'}else{'correct'}
  Check
  & "$root\regression.ps1" -Set $Version -Adaptive $adaptive -BenchName benchmark-production.exe -CandidateBenchName benchmark-production.exe -CorrectnessOnly -Batch $batch *> "$root\regression-$Version-$batch.log"
  if(!$?){throw "Replay failed $Version $batch"}
 }
 $gold=@(Import-Csv "$root\golden.csv");if($gold.Count -ne 168){throw 'golden coverage'}
 $hashes=@();$bad=@();$ae=@()
 foreach($row in $gold){
  $batch=if($row.mode -eq 'AE'){'adaptive'}else{'correct'}
  foreach($side in 'False','True'){
   $slot="$($row.case)-$side";$path="$root\runtime-regression-$Version-$batch\$slot\$($row.frame)"
   $sha=(Get-FileHash $path).Hash
   $hashes += [pscustomobject]@{batch="runtime-regression-$Version-$batch";slot=$slot;frame=$row.frame;sha=$sha}
   if($sha -ne $row.sha){$bad+=@{mode=$row.mode;case=$row.case;frame=$row.frame;side=$side;sha=$sha}}
  }
 }
 foreach($case in @($gold|Where-Object{$_.mode -eq 'AE'}|Select-Object -ExpandProperty case -Unique)){
  $base="$root\runtime-regression-$Version-adaptive"
  $b=@(Get-Content "$base\$case-False\adaptive.csv");$c=@(Get-Content "$base\$case-True\adaptive.csv")
  if($b.Count -ne 12 -or $c.Count -ne 12){throw 'AE coverage'}
  for($i=0;$i -lt 12;$i++){$ae+=@{case=$case;row=$i;equal=($b[$i] -ceq $c[$i]);baseline=$b[$i];candidate=$c[$i]}}
 }
 $unequal=@($ae|Where-Object{!$_.equal}).Count
 $hashes|Export-Csv "$root\hashes-$Version.csv" -NoTypeInformation
 $summary=@{version=$Version;candidate_frames=168;baseline_frames=168;golden_mismatches=$bad;ae_unequal=$unequal;pass=($bad.Count -eq 0 -and $unequal -eq 0)}
 $summary|ConvertTo-Json -Depth 7|Set-Content "$root\validation-$Version.json"
 # Get-Content strings carry large PowerShell ETS properties. Raw CSV already
 # preserves every field; serialize only the equality index here.
 $ae|Select-Object case,row,equal|ConvertTo-Json -Depth 3|Set-Content "$root\adaptive-$Version.json"
 Check
 $summary|ConvertTo-Json -Depth 7
}
if($Action -eq 'Timing'){
 Check
 $v=Get-Content "$root\validation-$Version.json" -Raw|ConvertFrom-Json
 if(!$v.pass){throw 'Timing forbidden: numerical regression failed'}
 foreach($batch in 'timing1','timing2'){
  Check
  & "$root\regression.ps1" -Set $Version -Adaptive 0 -BenchName benchmark-production.exe -CandidateBenchName benchmark-production.exe -TimingOnly -Batch $batch -TimingFrames 1000 *> "$root\regression-$Version-$batch.log"
  if(!$?){throw "Timing failed $Version $batch"}
 }
 Check
 Write-Output "$Version completed two 900/1080 ABBA batches"
}
if($Action -eq 'Collect'){
 $out="$root\collected-$Version"
 New-Item -ItemType Directory -Force $out|Out-Null
 foreach($batch in 'correct','adaptive','timing1','timing2'){
  $source="$root\runtime-regression-$Version-$batch"
  if(!(Test-Path $source)){continue}
  foreach($slot in Get-ChildItem $source -Directory){
   $dest="$out\runtime-regression-$Version-$batch\$($slot.Name)";New-Item -ItemType Directory -Force $dest|Out-Null
   Get-ChildItem $slot.FullName -File|Where-Object{$_.Extension -in '.csv','.log','.txt'}|Copy-Item -Destination $dest
  }
  Copy-Item "$root\regression-$Version-$batch.log" $out
 }
 Copy-Item "$root\hashes-$Version.csv","$root\validation-$Version.json","$root\adaptive-$Version.json" $out
 Compress-Archive "$out\*" "$root\collected-$Version.zip" -Force
}

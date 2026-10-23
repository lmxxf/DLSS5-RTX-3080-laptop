$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929'
$out="$root\collected"
New-Item -ItemType Directory -Force $out|Out-Null
foreach($batch in 'correct','adaptive'){
 $source="$root\runtime-regression-L-$batch"
 foreach($slot in Get-ChildItem $source -Directory){
  $dest="$out\runtime-regression-L-$batch\$($slot.Name)"
  New-Item -ItemType Directory -Force $dest|Out-Null
  Get-ChildItem $slot.FullName -File|Where-Object {$_.Extension -in '.csv','.log','.txt'}|Copy-Item -Destination $dest
 }
 Copy-Item "$root\regression-$batch.log" $out
}
Copy-Item "$root\hashes.csv","$root\snapshot.json" $out
Compress-Archive -Path "$out\*" -DestinationPath "$root\collected.zip" -Force
Get-FileHash "$root\collected.zip"

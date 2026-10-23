$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929'
$game='C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64'
if(Test-Path "$root\snapshot.json"){throw 'Snapshot exists; preserve the original evidence'}
New-Item -ItemType Directory -Force "$root\baseline\gfx1200","$root\baseline\gfx1201"|Out-Null
$hip="$game\DLSS5-AMD\native-game-tiled-assets\HIP"
$records=@()
foreach($arch in 'gfx1200','gfx1201'){
 $files=@(Get-ChildItem "$hip\$arch" -Filter '*.hsaco')
 if($files.Count -ne 30){throw "Expected 30 modules: $arch"}
 foreach($f in $files){
  $hash=(Get-FileHash $f.FullName).Hash
  Copy-Item $f.FullName "$root\baseline\$arch\$($f.Name)"
  if((Get-FileHash "$root\baseline\$arch\$($f.Name)").Hash -ne $hash){throw 'Copy mismatch'}
  $records+=@{path=$f.FullName;sha256=$hash;arch=$arch;name=$f.Name}
 }
}
foreach($f in @("$game\dlss5-amd.addon64","$game\dxgi.dll","$game\OptiScaler.ini","$game\DLSS5-AMD\native-game-flags.txt")){
 $records+=@{path=$f;sha256=(Get-FileHash $f).Hash}
}
$dll=Get-Item "$env:windir\System32\amd_comgr_3.dll"
$info=@{time=(Get-Date -Format o);files=$records;comgr=@{path=$dll.FullName;version=$dll.VersionInfo.FileVersion;sha256=(Get-FileHash $dll.FullName).Hash};processes=@(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile'}|Select-Object Id,ProcessName)}
$info|ConvertTo-Json -Depth 6|Set-Content "$root\snapshot.json"
Copy-Item "$game\DLSS5-AMD\native-game-flags.txt" "$root\base-flags.txt"
Compress-Archive -Path "$root\baseline" -DestinationPath "$root\baseline.zip"
Get-Content "$root\snapshot.json"

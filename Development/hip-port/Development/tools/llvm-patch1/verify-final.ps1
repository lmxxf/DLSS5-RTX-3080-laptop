$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-patch1-20260929'
$s=Get-Content "$root\snapshot.json" -Raw|ConvertFrom-Json
$n=0;foreach($f in $s.files){if((Get-FileHash $f.path).Hash -ne $f.sha256){throw "Installed file changed: $($f.path)"};$n++}
$moduleCount=0
foreach($set in 'O','P'){
 $m=Get-Content "$root\manifest-$set.json" -Raw|ConvertFrom-Json
 foreach($x in $m.modules|Where-Object{$_.target -eq 'gfx1201'}){if((Get-FileHash "$root\flat-$set\$($x.module).hsaco").Hash.ToLower() -ne $x.sha256){throw 'Lab module changed'};$moduleCount++}
}
@{installed_files_unchanged=$n;lab_modules_checked=$moduleCount;host_sha256=(Get-FileHash "$root\benchmark-production.exe").Hash;time=(Get-Date -Format o)}|ConvertTo-Json

$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend";$root="$lab\ffn-direct-production-modules"
New-Item -ItemType Directory -Force $root|Out-Null
foreach($arch in 'gfx1200','gfx1201'){
 New-Item -ItemType Directory -Force "$root\$arch"|Out-Null
 Copy-Item "$lab\dual-arch-modules\$arch\*.hsaco" "$root\$arch" -Force
}
foreach($name in 'multihead-fast-padded-wave','multihead-fast-padded-wave-packed'){
 & "$lab\ffn-direct-src\build-modules.ps1" -SourceDir "$lab\ffn-direct-src" -OutputDir $root -Compiler "$lab\dual-arch-src\rtc_compile.exe" -Only $name
}
# Recreate the complete manifests; -Only records only the rebuilt module in modules.json.
foreach($arch in 'gfx1200','gfx1201'){
 Remove-Item "$root\$arch\modules.json" -ErrorAction SilentlyContinue
 $rows=@(Get-ChildItem "$root\$arch\*.hsaco"|Sort-Object Name|ForEach-Object{(Get-FileHash $_.FullName).Hash.ToLowerInvariant()+'  '+$_.Name})
 [IO.File]::WriteAllLines("$root\$arch\SHA256SUMS",$rows)
 if($rows.Count -ne 24){throw 'Incomplete modules'}
}
$rows=@(foreach($arch in 'gfx1200','gfx1201'){Get-Content "$root\$arch\SHA256SUMS"|ForEach-Object{$_.Substring(0,66)+$arch+'/'+$_.Substring(66)}})
[IO.File]::WriteAllLines("$root\SHA256SUMS",$rows)
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie before GPU validation'}
$source=[IO.File]::ReadAllText("$r\validate-dual-arch.ps1").Replace('dual-arch-modules','ffn-direct-production-modules').Replace('dual-golden','directword-golden').Replace('dual-auto','directword-auto')
$check="$lab\ffn-direct-src\validate-production.ps1";[IO.File]::WriteAllText($check,$source)
& $check

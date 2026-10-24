$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend";$root="$lab\c256-frag-production-modules"
New-Item -ItemType Directory -Force $root|Out-Null
foreach($arch in 'gfx1200','gfx1201'){
 New-Item -ItemType Directory -Force "$root\$arch"|Out-Null
 Copy-Item "$lab\ffn-load-production-modules\$arch\*.hsaco" "$root\$arch" -Force
}
foreach($name in 'multihead-fast-padded-wave','multihead-fast-padded-wave-packed'){
 & "$lab\c256-frag-src\build-modules.ps1" -SourceDir "$lab\c256-frag-src" -OutputDir $root -Compiler "$lab\dual-arch-src\rtc_compile.exe" -Only $name
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
$source=[IO.File]::ReadAllText("$r\validate-dual-arch.ps1").Replace('dual-arch-modules','c256-frag-production-modules').Replace('dual-golden','c256frag-golden').Replace('dual-auto','c256frag-auto')
$source=$source.Replace('benchmark_dual.exe','benchmark_c256frag_production.exe').Replace('reference_dual.exe','reference_c256frag.exe').Replace("'DLSS5_HIP_DECODER_BYTE=1'","'DLSS5_HIP_DECODER_BYTE=1','DLSS5_HIP_MH_FFN_FRAG256=1'").Replace("'--decoder-byte'","'--decoder-byte','--mh-ffn-frag256'")
$check="$lab\c256-frag-src\validate-production.ps1";[IO.File]::WriteAllText($check,$source)
& $check

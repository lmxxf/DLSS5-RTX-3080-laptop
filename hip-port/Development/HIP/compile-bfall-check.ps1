$ErrorActionPreference='Stop'
# Recompile the three files with the flipped source defaults and no extra define; the .s must match bfall-*.hsaco.s except the cuid.
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$pre="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"
foreach($f in 'deep_fast.hip','multihead_fast_padded.hip','multihead_fused_attention.hip'){
 $n='bfall2-'+[IO.Path]::GetFileNameWithoutExtension($f)
 [IO.File]::WriteAllText("$r\$n.generated.hip",$pre+[IO.File]::ReadAllText("$r\src-bfall2\$f")+"`n",$utf8)
 & "$r\..\rtc_compile.exe" "$r\$n.hsaco" "$r\$n.generated.hip" comgr | Out-Null
 if($LASTEXITCODE){throw "COMGR failed $n"}
 $a=(Get-Content "$r\$n.hsaco.s")|Where-Object{$_ -notmatch 'cuid|generated\.hip'}
 $b=(Get-Content ("$r\bfall-"+[IO.Path]::GetFileNameWithoutExtension($f)+".hsaco.s"))|Where-Object{$_ -notmatch 'cuid|generated\.hip'}
 $d=Compare-Object $a $b
 Write-Output ("$f plain-default vs bfall: differing lines="+@($d).Count)
}

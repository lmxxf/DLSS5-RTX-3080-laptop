# Compare against the accepted direct-FP8-input build, with identical production flags.
param([switch]$Timing,[switch]$Recheck)
$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}
$stem='ffnpre256';$build='ffn-prefetch-build'
$baseline="$lab\ffn-load-production-modules\gfx1201";$candidate="$r\$stem-modules"
New-Item -ItemType Directory -Force $candidate|Out-Null
Copy-Item "$baseline\*.hsaco" $candidate -Force
Copy-Item "$lab\$build\gfx1201\multihead-fast-padded-wave-packed.hsaco" $candidate -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0'
if($Timing){
 $tag=if($Recheck){"$stem-recheck"}else{$stem};$frames=if($Recheck){120}else{80}
 foreach($height in 900,1080){foreach($i in 0..3){
  $useCandidate=if($Recheck){$i -in 0,3}else{$i -in 1,2};$m=if($useCandidate){$candidate}else{$baseline}
  & "$r\profile-1080.ps1" -Frames $frames -Tag "$tag-$height-$i" -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $m -Runner benchmark_dual.exe -TimingOnly
 }}
 foreach($height in 900,1080){$hashes=@(foreach($i in 0..3){(Import-Csv "$r\profile1080\$tag-$height-$i-summary.csv").hash});if(@($hashes|Select-Object -Unique).Count -ne 1){throw 'Timing output mismatch'}}
}else{
 $source=[IO.File]::ReadAllText("$r\validate-c32-register-ex.ps1");$needle='$f="$work\check-flags.txt";'
 if(!$source.Contains($needle)){throw 'Validation harness changed'}
 $source=$source.Replace($needle,('$flags+=@('''+$flags.Replace(';',"','")+''');'+$needle))
 $check="$lab\ffn-prefetch-src\validate-matched.ps1";[IO.File]::WriteAllText($check,$source)
 & $check -Candidate "$stem-modules" -Baseline '..\ffn-load-production-modules\gfx1201' -Tag $stem -Runner benchmark_dual.exe
 & $check -Extended -Candidate "$stem-modules" -Baseline '..\ffn-load-production-modules\gfx1201' -Tag $stem -Runner benchmark_dual.exe
}

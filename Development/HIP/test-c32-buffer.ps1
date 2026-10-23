# Compare against the accepted direct-FP8-input build, with identical production flags.
param([switch]$Timing,[switch]$Recheck,[ValidateSet('both','read','write')][string]$Variant='both')
$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}
$stem=if($Variant -eq 'both'){'c32buf'}else{"c32buf-$Variant"};$build=if($Variant -eq 'both'){'c32-buffer-build'}else{"c32-buffer-$Variant-build"}
$baseline="$lab\c256-frag-production-modules\gfx1201";$candidate="$r\$stem-modules"
New-Item -ItemType Directory -Force $candidate|Out-Null
Copy-Item "$baseline\*.hsaco" $candidate -Force
Copy-Item "$lab\$build\gfx1201\c32_fused_ffn_attention-packed.hsaco" $candidate -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0;DLSS5_HIP_MH_FFN_FRAG256=1'
if($Timing){
 $tag=if($Recheck){"$stem-recheck"}else{$stem};$frames=if($Recheck){240}else{80}
 foreach($height in 900,1080){foreach($i in 0..3){
  $useCandidate=if($Recheck){$i -in 0,3}else{$i -in 1,2};$m=if($useCandidate){$candidate}else{$baseline}
  & "$r\profile-1080.ps1" -Frames $frames -Tag "$tag-$height-$i" -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $m -Runner benchmark_c256frag_production.exe -TimingOnly
 }}
 foreach($height in 900,1080){$hashes=@(foreach($i in 0..3){(Import-Csv "$r\profile1080\$tag-$height-$i-summary.csv").hash});if(@($hashes|Select-Object -Unique).Count -ne 1){throw 'Timing output mismatch'}}
}else{
 $source=[IO.File]::ReadAllText("$r\validate-c32-register-ex.ps1");$needle='$f="$work\check-flags.txt";'
 if(!$source.Contains($needle)){throw 'Validation harness changed'}
 $source=$source.Replace($needle,('$flags+=@('''+$flags.Replace(';',"','")+''');'+$needle))
 $check="$lab\c32-buffer-src\validate-matched.ps1";[IO.File]::WriteAllText($check,$source)
 & $check -Candidate "$stem-modules" -Baseline '..\c256-frag-production-modules\gfx1201' -Tag $stem -Runner benchmark_c256frag_production.exe
 & $check -Extended -Candidate "$stem-modules" -Baseline '..\c256-frag-production-modules\gfx1201' -Tag $stem -Runner benchmark_c256frag_production.exe
}

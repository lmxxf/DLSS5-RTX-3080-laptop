# Isolated host routes MH_FFN_FRAG to C256 only; both A/B variants use the same host/module set.
param([switch]$Timing,[switch]$Recheck)
$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend";$m="$r\c256-fragment-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}
New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$lab\ffn-load-production-modules\gfx1201\*.hsaco" $m -Force
Copy-Item "$lab\c256-frag-build\gfx1201\multihead-fast-padded-wave-packed.hsaco" $m -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0;DLSS5_HIP_MH_FFN_FRAG=0'
if($Timing){
 $tag=if($Recheck){'c256frag-recheck'}else{'c256frag'};$frames=if($Recheck){120}else{80}
 foreach($height in 900,1080){foreach($i in 0..3){
  $on=if($Recheck){[int]($i -in 0,3)}else{[int]($i -in 1,2)}
  & "$r\profile-1080.ps1" -Frames $frames -Tag "$tag-$height-$i" -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height;DLSS5_HIP_MH_FFN_FRAG=$on" -Modules $m -Runner benchmark_c256frag.exe -TimingOnly
 }}
 foreach($height in 900,1080){$hashes=@(foreach($i in 0..3){(Import-Csv "$r\profile1080\$tag-$height-$i-summary.csv").hash});if(@($hashes|Select-Object -Unique).Count -ne 1){throw 'Timing output mismatch'}}
}else{
 $source=[IO.File]::ReadAllText("$r\validate-c32-register-ex.ps1");$needle='$f="$work\check-flags.txt";'
 if(!$source.Contains($needle)){throw 'Validation harness changed'}
 $source=$source.Replace($needle,('$flags+=@('''+$flags.Replace(';',"','")+''');'+$needle))
 $check="$lab\c256-frag-src\validate-matched.ps1";[IO.File]::WriteAllText($check,$source)
 & $check -Candidate c256-fragment-modules -Baseline c256-fragment-modules -Tag c256frag -Runner benchmark_c256frag.exe -CandidateFlags 'DLSS5_HIP_MH_FFN_FRAG=1'
 & $check -Extended -Candidate c256-fragment-modules -Baseline c256-fragment-modules -Tag c256frag -Runner benchmark_c256frag.exe -CandidateFlags 'DLSS5_HIP_MH_FFN_FRAG=1'
}

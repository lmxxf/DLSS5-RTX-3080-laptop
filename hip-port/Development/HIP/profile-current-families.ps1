# Duplicate each pure kernel in a family once in the real pipeline; compare to adjacent unduplicated runs.
# Marginal times include cache/launch effects and must not be summed as a network time breakdown.
param([string]$Heights='900,1080',[string]$Families='c32,vit,c256,post,c64,c128,attn64,attn128,attn256,split,qkv512,attn512,decoder,pool',[int]$Frames=160,[int]$WarmupFrames=32,[string]$Tag='current-map')
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$work="$r\profile1080"
$modules='D:\DLSSNR-Lab\c256-frag-production-modules'
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0;DLSS5_HIP_MH_FFN_FRAG256=1;DLSS5_HIP_GRAPH=0'
$expected=@{900='75AABA5EF94368353F3F17C034B53918151AA2EBC98FF870B2A057D08AE910AB';1080='1DE20C219105CC281CBA1364A0A21D0DDC4510A95458EC0CA3B8C893EA54F23A'}
$all=@();$margins=@()
foreach($heightText in $Heights.Split(',')){
 $height=[int]$heightText;if(!$expected.ContainsKey($height)){throw 'Unsupported tier'}
 $sequence=@('none');foreach($family in $Families.Split(',')){$sequence+=@($family,'none')}
 $runs=@();$i=0
 foreach($family in $sequence){
  $runTag="$Tag-$height-$i"
  & "$r\profile-1080.ps1" -Families $family -Frames $Frames -WarmupFrames $WarmupFrames -Tag $runTag -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $modules -Runner benchmark_c256frag_production.exe -TimingOnly
  $row=Import-Csv "$work\$runTag-summary.csv"
  if($row.hash -ne $expected[$height]){throw "Duplicating $family changed the output"}
  $entry=[pscustomobject]@{height=$height;index=$i;family=$family;median_ms=[double]$row.median_ms;p10_ms=[double]$row.p10_ms;p90_ms=[double]$row.p90_ms;hash=$row.hash;tag=$runTag};$runs+=$entry;$all+=$entry
  $all|Export-Csv "$work\$Tag-runs.csv" -NoTypeInformation
  if($i -ge 2 -and $family -eq 'none'){
   $before=$runs[$i-2];$test=$runs[$i-1];$after=$runs[$i]
   $base=($before.median_ms+$after.median_ms)/2
   $m=[pscustomobject]@{height=$height;family=$test.family;baseline_before_ms=$before.median_ms;duplicate_ms=$test.median_ms;baseline_after_ms=$after.median_ms;marginal_ms=$test.median_ms-$base;baseline_drift_ms=[Math]::Abs($after.median_ms-$before.median_ms);duplicate_p90_p10_ms=$test.p90_ms-$test.p10_ms}
   $margins+=$m;$margins|Export-Csv "$work\$Tag-margins.csv" -NoTypeInformation
   'MARGINAL '+($m|ConvertTo-Json -Compress)
  }
  $i++
 }
}

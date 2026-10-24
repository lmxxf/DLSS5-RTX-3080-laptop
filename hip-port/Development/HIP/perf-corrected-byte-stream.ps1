$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\decoder-tail-stream-modules"
foreach($height in 720,900,1080){
 $expected=''
 foreach($i in 0..3){
  $flags="DLSS5_NETWORK_HEIGHT=$height;DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1"
  if($i -in @(1,2)){$flags+=';DLSS5_HIP_MH_BYTE_STREAM=1'}
  $tag="corrected-stream-$height-$i"
  & "$r\profile-1080.ps1" -Families none -Frames 80 -Tag $tag -ExtraFlag $flags -Modules $m -Runner benchmark_decoder_tail.exe -TimingOnly
  $row=Import-Csv "$r\profile1080\$tag-summary.csv"
  if(!$expected){$expected=$row.hash}elseif($row.hash -ne $expected){throw 'Output changed'}
 }
}

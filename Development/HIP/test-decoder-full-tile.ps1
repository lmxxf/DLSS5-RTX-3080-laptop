$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m="$r\decoder-full-tile-modules"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
New-Item -ItemType Directory -Force $m|Out-Null;Copy-Item "$r\full-byte-modules\*.hsaco" $m -Force
& "$r\..\rtc_compile.exe" "$m\deep_fast-packed.hsaco" "$r\decoder-full-tile.hip" comgr
if($LASTEXITCODE){throw 'Compile failed'}
& "$r\test_decoder_tail.exe" 'D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets' $m
if($LASTEXITCODE){throw 'Tail coverage failed'}
foreach($height in 900,1080){
 $expected=''
 foreach($i in 0..3){
  $modules=if($i -in @(1,2)){$m}else{"$r\full-byte-modules"}
  $flags="DLSS5_NETWORK_HEIGHT=$height;DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1"
  $tag="fulltile-$height-$i"
  & "$r\profile-1080.ps1" -Families none -Frames 80 -Tag $tag -ExtraFlag $flags -Modules $modules -Runner benchmark_full_byte.exe -TimingOnly
  $row=Import-Csv "$r\profile1080\$tag-summary.csv"
  if(!$expected){$expected=$row.hash}elseif($row.hash -ne $expected){throw 'Output changed'}
 }
}

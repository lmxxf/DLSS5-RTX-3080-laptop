$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$dest="$r\main-reuse-modules";$results="$r\main-reuse-results";$assets='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD'
function Idle {if(Get-Process SB-Win64-Shipping,Magpie,re9,LOP-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}}
Idle;New-Item -ItemType Directory -Force $dest,$results|Out-Null
Copy-Item "$r\vit-residual-adaptive-r3-modules\*.hsaco" $dest
Copy-Item 'D:\DLSSNR-Lab\main-reuse-build\gfx1201\deep_fast-packed.hsaco' $dest
$proof=@()
foreach($height in 900,1080){foreach($seq in 0,1,6){foreach($mode in 0,1){
 foreach($side in 'r3','main'){
  Idle;$folder="$results\$height-$seq-$mode-$side";New-Item -ItemType Directory -Force $folder|Out-Null
  $flags=@(Get-Content "$assets\native-game-flags.txt")+@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1','DLSS5_HIP_DECODER_BYTE=1','DLSS5_HIP_VIT_BYTE_STREAM=0','DLSS5_HIP_MH_FFN_FRAG256=1','DLSS5_HIP_GRAPH=0','DLSS5_SHOW_FPS=0','DLSS5_PRE_UPSCALE=0',"DLSS5_NETWORK_HEIGHT=$height","DLSS5_VIT_ADAPTIVE=$mode",'DLSS5_VIT_REUSE_PERIOD=4','DLSS5_VIT_REUSE_HOTKEY=0',"DLSS5_VIT_REUSE_GAIN=$(if($side -eq 'r3'){"$r\vit-residual-scales\gain.f32"}else{''})",'DLSS5_VIT_ADAPTIVE_LOG=',"DLSS5_RESIDUAL_SEQUENCE=$seq",'DLSS5_RESIDUAL_RGB=1')
  [IO.File]::WriteAllLines("$folder\flags.txt",$flags)
  $runner=if($side -eq 'r3'){'benchmark_vit_adaptive_r3.exe'}else{'benchmark_main_reuse.exe'};$modules=if($side -eq 'r3'){"$r\vit-residual-adaptive-r3-modules"}else{$dest}
  & "$r\$runner" "$assets\native-game-tiled-assets" "$folder\flags.txt" "$r\live-menu-before.f16" "$folder\rgb" 12 1 $modules 0 0 0 0 > "$folder\run.log"
  if($LASTEXITCODE){throw "Failed $folder"};Idle
  $rows=@(Import-Csv "$folder\rgb.csv");if($rows.Count -ne 12 -or @($rows|Where-Object{[int]$_.invalid -ne 0}).Count){throw 'Invalid frames'}
 }
 $a="$results\$height-$seq-$mode-r3";$b="$results\$height-$seq-$mode-main"
 $files=@(Get-ChildItem $a -Filter '*frame-*.f16');if($files.Count -ne 12){throw 'Expected12 RGB frame files'}
 foreach($f in $files){if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash "$b\$($f.Name)").Hash){throw "Frame mismatch $height/$seq/$mode/$($f.Name)"}}
 $proof+=[pscustomobject]@{height=$height;sequence=$seq;mode=$mode;matching_frames=$files.Count};$proof[-1]|ConvertTo-Json -Compress
}}}
$proof|ConvertTo-Json|Set-Content "$results\proof.json"

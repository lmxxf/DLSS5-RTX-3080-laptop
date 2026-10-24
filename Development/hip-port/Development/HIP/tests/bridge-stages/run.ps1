$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$d="$r\bridge-stages";$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
function Idle{if(Get-Process LOP-Win64-Shipping,SB-Win64-Shipping,OnimushaWotS,re9,Magpie -ErrorAction SilentlyContinue){throw 'Game running'}}
Idle;New-Item -ItemType Directory -Force "$d\modules\gfx1201"|Out-Null
Copy-Item "$r\network-fixed-shapes\selected-modules\*.hsaco" "$d\modules\gfx1201"
foreach($case in @(@(900,0),@(1080,0),@(900,1))){
 Idle;$height=$case[0];$graph=$case[1];$w=if($height -eq 900){1600}else{1920};$h=if($height -eq 900){960}else{1152}
 $modules=if($height -eq 900){"$d\modules"}else{"$r\network-fixed-shapes\selected-modules"}
 & "$d\test.exe" $a $modules "$r\network-timeline\$height\flags.txt" "$r\network-timeline\$height\input.f32" "$r\network-timeline\$height\expected.f32" $w $h $graph > "$d\bridge-$height-g$graph.log"
 if($LASTEXITCODE){Get-Content "$d\bridge-$height-g$graph.log";throw 'Bridge stage test failed'}
 Get-Content "$d\bridge-$height-g$graph.log" | Select-String '^(DEVICE|PASS|graph_stats)'
}

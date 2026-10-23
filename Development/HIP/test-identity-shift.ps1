param([uint32]$Seed=0,[string]$HistoryFile='',[string]$ExpectedHash='7B9591437302EA680C87684B3C690EDD7FA76B56A1F7ACA0C11773464512E29D')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($i in 0..3){
 $extra=@('--seed',"$Seed");if($HistoryFile){$extra+=@('--history',$HistoryFile)};if($i -in @(1,2)){$extra+='--elide-identity-shift'}
& "$r\reference_current.exe" $a "$r\vit-layout-modules" "$r\input900.rgba32f" "$a\noise.f32" "$r\identity-shift.f32" --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --packed-c32 --fp8-normalized --fp8-ffn --fp8-av --fp8-deep --fp8-middle --half-c32 --crop-c32 --fused-qkv-norm --fused-mh-ffn --tiled-mh-ffn-large --mapped-c32 --vit-blocked --vit-contract-blocked --vit-weight-mask 1 --vit-pack-input --repeat 6 @extra > "$r\identity-shift.log"
 if($LASTEXITCODE){throw 'Run failed'}
 if((Get-FileHash "$r\identity-shift.f32").Hash -ne $ExpectedHash){throw 'Mismatch'}
 Copy-Item "$r\identity-shift.log" "$r\identity-shift-$i.log"
 Write-Output "ROUND=$i"
 Get-Content "$r\identity-shift.log" | Select-String '^iteration='
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

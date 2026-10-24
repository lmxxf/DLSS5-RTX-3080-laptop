param([uint32]$Seed=0,[string]$HistoryFile='',[string]$ExpectedHash='7B9591437302EA680C87684B3C690EDD7FA76B56A1F7ACA0C11773464512E29D')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$m="$r\c32-output8-modules"
New-Item -ItemType Directory -Force $m | Out-Null
Copy-Item "$r\c32-input-dword-release-modules\*.hsaco" $m -Force
foreach($i in 0..3){
 $source=if($i -in @(1,2)){"$r\c32-output8.hsaco"}else{"$r\c32-input-dword-release-modules\c32_fused_ffn_attention-packed.hsaco"}
 Copy-Item $source "$m\c32_fused_ffn_attention-packed.hsaco" -Force
 $extra=@('--seed',"$Seed");if($HistoryFile){$extra+=@('--history',$HistoryFile)};$extra+='--elide-identity-shift'
& "$r\reference_current.exe" $a $m "$r\input900.rgba32f" "$a\noise.f32" "$r\c32-output8.f32" --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --packed-c32 --fp8-normalized --fp8-ffn --fp8-av --fp8-deep --fp8-middle --half-c32 --crop-c32 --fused-qkv-norm --fused-mh-ffn --tiled-mh-ffn-large --mapped-c32 --vit-blocked --vit-contract-blocked --vit-weight-mask 1 --vit-pack-input --repeat 6 @extra > "$r\c32-output8.log"
 if($LASTEXITCODE){throw 'Run failed'}
 if((Get-FileHash "$r\c32-output8.f32").Hash -ne $ExpectedHash){throw 'Mismatch'}
 Copy-Item "$r\c32-output8.log" "$r\c32-output8-$i.log"
 Write-Output "ROUND=$i"
 Get-Content "$r\c32-output8.log" | Select-String '^iteration='
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

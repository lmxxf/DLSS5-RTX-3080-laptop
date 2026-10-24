param([string]$Flags='compare-hip-sync-flags.txt',[string]$Modules='vit-layout-modules',[string]$Runner='queued_frame_old.exe',[string]$Name='queued-test',[int]$Async=0,[int]$Rotate=0,[int]$Temporal=0,[int]$VaryContent=0)
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$r='D:\DLSSNR-Lab\hip-backend'
& "$r\$Runner" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" (Join-Path $r $Flags) (Join-Path $r $Modules) "$r\live-menu-before.f16" "$r\$Name" $Async $Rotate $Temporal $VaryContent > "$r\$Name.log"
if($LASTEXITCODE){Get-Content "$r\$Name.log" -Tail 8;throw 'Queued frame probe failed'}
Get-Content "$r\$Name.log"
Write-Output "SHA256=$((Get-FileHash "$r\$Name.f16").Hash)"

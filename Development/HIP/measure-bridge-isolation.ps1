param([ValidateSet(0,1)][int]$Graph=0,[string]$Tag='bridge-isolate')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$flagLines=@(Get-Content "$r\rebind-async-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_GRAPH='});$flagLines+="DLSS5_HIP_GRAPH=$Graph";$flagLines|Set-Content "$r\$Tag-flags.txt"
& "$r\benchmark_bridge_isolate.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\$Tag-flags.txt" "$r\live-menu-before.f16" "$r\$Tag" 40 0 "$r\prefix-direct-input-release-modules" 0 1 > "$r\$Tag.log"
if($LASTEXITCODE){Get-Content "$r\$Tag.log" -Tail 8;throw 'Isolation failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
$rows=@(Import-Csv "$r\$Tag.csv"|Where-Object{[int]$_.frame -ge 5})
$t=@($rows|ForEach-Object{[double]$_.wall_ms}|Sort-Object)
Write-Output "FULL_FRAME median_ms=$($t[[int]($t.Count/2)]) temporal=0 edges_only=1"
Get-Content "$r\$Tag.log"|Select-String 'BRIDGE_ISOLATE|BRIDGE_FULL_AFTER|graph_stats'
if($Graph -eq 1 -and !((Get-Content "$r\$Tag.log") -match 'graph_stats builds=[1-9][0-9]* replays=[1-9][0-9]*')){throw 'Graph replay not observed'}

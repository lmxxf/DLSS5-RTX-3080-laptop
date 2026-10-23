$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$r='D:\DLSSNR-Lab\hip-backend'
foreach($mode in @('hlsl-sync','hlsl-async','hip-sync','hip-graph')){
 $isHip=$mode.StartsWith('hip');$async=if($mode -eq 'hlsl-async'){1}else{0};$graph=if($mode -eq 'hip-graph'){1}else{0}
 $f=@(Get-Content "$r\frame-profile-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_TEST_ASYNC_SUBMIT=|^DLSS5_GAME_PROBE=|^DLSS5_HIP_GRAPH='})
 $f+="DLSS5_TEST_ASYNC_SUBMIT=$async";$f+='DLSS5_GAME_PROBE=0';$f+="DLSS5_HIP_GRAPH=$graph";$f|Set-Content "$r\compare-$mode-flags.txt"
 $exe=if($isHip){'benchmark_live_capture.exe'}else{'benchmark_live_hlsl.exe'}
 & "$r\$exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\compare-$mode-flags.txt" "$r\live-menu-before.f16" "$r\compare-$mode" 40 1 "$r\half-c32-modules" > "$r\compare-$mode.log"
 if($LASTEXITCODE){throw "Failed mode=$mode"}
 $rows=@(Import-Csv "$r\compare-$mode.csv")
 if(@($rows|Where-Object{[int]$_.invalid -ne 0}).Count){throw 'Nonfinite output'}
 $t=@($rows|Where-Object{[int]$_.frame -ge 5}|ForEach-Object{[double]::Parse($_.wall_ms,[Globalization.CultureInfo]::InvariantCulture)}|Sort-Object)
 Write-Output "RESULT mode=$mode hot_samples=$($t.Count) median_ms=$($t[17]) sha256=$((Get-FileHash "$r\compare-$mode.f16").Hash)"
 Get-Content "$r\compare-$mode.log"|Select-String 'graph_stats'
}

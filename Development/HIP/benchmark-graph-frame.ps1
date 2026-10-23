param([int]$Frames=40,[int]$ResetEvery=0,[string]$Tag='graph-abba',
 [string]$Runner='benchmark_live_capture.exe',[string]$Modules='edge-modules',[string]$ConfigFile='frame-profile-flags.txt',[string]$ExpectedHash='')
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$r='D:\DLSSNR-Lab\hip-backend';$work=Join-Path $r $Tag
New-Item -ItemType Directory -Force $work|Out-Null
$hash=$null;$rows=@()
for($round=0;$round -lt 4;$round++){
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
 $v=@(0,1,1,0)[$round];$prefix=Join-Path $work "$round-$v"
 $flags=@(Get-Content (Join-Path $r $ConfigFile)|Where-Object{$_ -notmatch '^DLSS5_HIP_GRAPH=|^DLSS5_GAME_PROBE='})
 $flags+="DLSS5_HIP_GRAPH=$v";$flags+='DLSS5_GAME_PROBE=0';$flags|Set-Content "$prefix-flags.txt"
 & (Join-Path $r $Runner) "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$prefix-flags.txt" "$r\live-menu-before.f16" $prefix $Frames 1 (Join-Path $r $Modules) $ResetEvery > "$prefix.log"
 if($LASTEXITCODE){throw "Frame benchmark failed round=$round"}
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard timings'}
 $actual=(Get-FileHash "$prefix.f16").Hash
 if($ExpectedHash -and $actual -ne $ExpectedHash){throw 'Reference HDR mismatch'}
 if($null -eq $hash){$hash=$actual}elseif($actual -ne $hash){throw 'Final HDR mismatch'}
 $stats=@(Get-Content "$prefix.log"|Select-String 'graph_stats')
 if($v -eq 1 -and !($stats -match 'replays=[1-9][0-9]*')){throw 'Graph replay not observed'}
 $stats
 foreach($row in (Import-Csv "$prefix.csv")){
  if([int]$row.invalid -ne 0){throw 'Nonfinite output'}
  if([int]$row.frame -ge 5){$rows+=[pscustomobject]@{round=$round;graph=$v;frame=$row.frame;ms=[double]::Parse($row.wall_ms,[Globalization.CultureInfo]::InvariantCulture)}}
 }
 Write-Output "PASS round=$round graph=$v sha256=$actual"
}
$rows|Export-Csv "$work\timings.csv" -NoTypeInformation
foreach($v in 0,1){$t=@($rows|Where-Object {$_.graph -eq $v}|ForEach-Object {$_.ms}|Sort-Object);$n=$t.Count;Write-Output "RESULT graph=$v hot_samples=$n median_ms=$(($t[[int]($n/2)-1]+$t[[int]($n/2)])/2)"}

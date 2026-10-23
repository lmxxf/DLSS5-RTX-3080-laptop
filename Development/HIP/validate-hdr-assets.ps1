param([string]$Assets='',[string]$Runner='benchmark_live_capture.exe',[string]$Modules='c32-mapped-modules',[string]$Name='hdr-validation',[string]$Flags='compare-hip-sync-flags.txt',
 [ValidateRange(1,10000)][int]$Frames=40,[int]$ResetEvery=0,[string]$ExpectedHash='',[ValidateSet(0,1)][int]$EdgesOnly=0)
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$r='D:\DLSSNR-Lab\hip-backend';$prefix=Join-Path $r $Name
$extra=@();if($EdgesOnly){$extra+="1"}
$assetsDir=if($Assets){$Assets}else{"$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets"};& (Join-Path $r $Runner) $assetsDir (Join-Path $r $Flags) "$r\live-menu-before.f16" $prefix $Frames 1 (Join-Path $r $Modules) $ResetEvery @extra > "$prefix.log"
if($LASTEXITCODE){throw 'HDR benchmark failed'}
$hash=(Get-FileHash "$prefix.f16").Hash
if($ExpectedHash -and $hash -ne $ExpectedHash){throw 'HDR output changed'}
$rows=@(Import-Csv "$prefix.csv")
$checked=@($rows|Where-Object{!$_.PSObject.Properties['checked'] -or $_.checked -eq '1'})
if(!$EdgesOnly -and $checked.Count -ne $rows.Count){throw 'Incomplete frame checks'}
if($EdgesOnly -and $checked.Count -ne [Math]::Min(2,$Frames)){throw 'Missing edge checks'}
if(@($checked|Where-Object{[int]$_.invalid -ne 0}).Count){throw 'Nonfinite HDR output'}
$t=@($rows|Where-Object{[int]$_.frame -ge 5}|ForEach-Object{[double]::Parse($_.wall_ms,[Globalization.CultureInfo]::InvariantCulture)}|Sort-Object)
if(!$t.Count){throw 'No hot samples'}
$median=if($t.Count%2){$t[[int][Math]::Floor($t.Count/2)]}else{($t[$t.Count/2-1]+$t[$t.Count/2])/2}
$scope=if($EdgesOnly){"sampled_finite=1 checked_frames=$($checked.Count)"}else{"finite=1"}
Write-Output "HDR name=$Name hot_median=$median $scope hash=$hash"

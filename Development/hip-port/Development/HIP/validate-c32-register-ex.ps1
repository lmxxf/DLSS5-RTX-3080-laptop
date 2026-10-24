param([switch]$Extended,[string]$Candidate='c32-register-ex-modules',[string]$Baseline='', [string]$Tag='regex',[string]$CandidateFlags='', [int]$OnlyHeight=0,[string]$Runner='benchmark1080.exe')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$base='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD'
$work="$r\profile1080";$rows=@()
$cases=if($Extended){@(@(900,0,123,0),@(1080,0,123,0),@(900,8,123,1),@(1080,8,123,1),@(900,8,9876,2),@(1080,8,9876,2))}else{@(@(720,0,0,0),@(720,8,0,0),@(900,0,0,0),@(900,8,0,0),@(1080,0,0,0),@(1080,8,0,0))}
foreach($case in $cases){
 $height,$reset,$seed,$pattern=$case
 if($OnlyHeight -and $height -ne $OnlyHeight){continue}
 $flags=@(Get-Content "$base\native-game-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_(NETWORK_HEIGHT|SHOW_FPS|NOTICE)='})+@("DLSS5_NETWORK_HEIGHT=$height",'DLSS5_SHOW_FPS=0','DLSS5_NOTICE=0')
 $f="$work\check-flags.txt";[IO.File]::WriteAllLines($f,$flags)
 $expected=''
 foreach($variant in 'base','candidate'){
  $extra=if($variant -eq 'candidate' -and $CandidateFlags){@($CandidateFlags.Split(';'))}else{@()}
  [IO.File]::WriteAllLines($f,($flags+$extra))
  if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
  $m=if($variant -eq 'base'){$(if($Baseline){"$r\$Baseline"}else{"$base\native-game-tiled-assets\HIP"})}else{"$r\$Candidate"}
  $prefix="$work\$Tag-check-$height-$reset-$seed-$pattern-$variant"
  & "$r\$Runner" "$base\native-game-tiled-assets" $f "$r\live-menu-before.f16" $prefix 24 1 $m $reset 0 $seed $pattern > "$prefix.log"
  if($LASTEXITCODE){throw 'Validation runner failed'}
  $csv=@(Import-Csv "$prefix.csv");if($csv.Count -ne 24 -or @($csv|Where-Object{[int]$_.invalid -ne 0 -or $_.checked -ne '1'}).Count){throw 'Missing/nonfinite frame'}
  $hash=(Get-FileHash "$prefix.f16").Hash;$first=(Get-FileHash "$prefix-first.f16").Hash
  if($variant -eq 'base'){$expected=$hash;$expectedFirst=$first}else{if($hash -ne $expected -or $first -ne $expectedFirst){throw 'First/final output mismatch'}}
  $row=[pscustomobject]@{height=$height;reset=$reset;seed=$seed;pattern=$pattern;variant=$variant;hash=$hash;first=$first};$rows+=$row;$row|ConvertTo-Json -Compress
 }
}
$suffix=if($Extended){'extended'}else{'validation'}
$rows|Export-Csv "$work\$Tag-$suffix.csv" -NoTypeInformation

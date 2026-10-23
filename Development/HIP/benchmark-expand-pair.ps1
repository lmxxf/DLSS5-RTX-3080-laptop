param([string]$Root='D:\DLSSNR-Lab\hip-backend',
 [string]$Assets='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets')
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Close Stellar Blade before offline GPU timing.'}
$work=Join-Path $Root 'expand-pair-test'
New-Item -ItemType Directory -Force $work | Out-Null
$modules=Join-Path $work 'modules'
New-Item -ItemType Directory -Force $modules | Out-Null
Copy-Item "$Root\repro-modules\*.hsaco" $modules -Force
$rows=@();$expected=$null
foreach($round in 0..3){
 $variant=@('base','pair','pair','base')[$round]
 Copy-Item "$Root\expand-$variant.hsaco" "$modules\deep_fast-packed.hsaco" -Force
 $output=Join-Path $work "$round-$variant.f32"
 $log=& "$Root\reference_network.exe" $Assets $modules "$Root\input900.rgba32f" "$Assets\noise.f32" $output --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --repeat 6 2>&1
 if($LASTEXITCODE -ne 0){throw ($log -join "
")}
 $log | Set-Content "$work\$round-$variant.log"
 $hash=(Get-FileHash $output).Hash
 if($null -eq $expected){$expected=$hash}elseif($hash -ne $expected){throw 'Full network output mismatch'}
 foreach($line in $log){if("$line" -match '^iteration=(\d+) wall_seconds=([\d.]+)'){
  $rows += [pscustomobject]@{round=$round;variant=$variant;iteration=[int]$Matches[1];ms=1000*[double]::Parse($Matches[2],[Globalization.CultureInfo]::InvariantCulture)}
 }}
 Write-Output "PASS round=$round variant=$variant hash=$hash"
}
$rows | Export-Csv "$work\timings.csv" -NoTypeInformation
foreach($variant in @('base','pair')){
 $hot=@($rows | Where-Object {$_.variant -eq $variant -and $_.iteration -gt 0} | ForEach-Object {$_.ms} | Sort-Object)
 Write-Output "RESULT variant=$variant median_ms=$(($hot[4]+$hot[5])/2)"
}

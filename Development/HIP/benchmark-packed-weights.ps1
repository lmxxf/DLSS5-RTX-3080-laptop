param(
 [Parameter(Mandatory=$true)][string]$Runner,
 [Parameter(Mandatory=$true)][string]$Assets,
 [Parameter(Mandatory=$true)][string]$Modules,
 [Parameter(Mandatory=$true)][string]$InputFile,
 [Parameter(Mandatory=$true)][string]$Noise,
 [Parameter(Mandatory=$true)][string]$OutputDir,
 [ValidateRange(3,100)][int]$Repeats=6
)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force $OutputDir | Out-Null
$rows=@(); $hash=$null
# ABBA reduces order/clock bias; every fresh process has one excluded cold iteration.
$variants=@('baseline','packed','packed','baseline')
for($round=0;$round -lt $variants.Count;$round++){
 $variant=$variants[$round];$prefix=Join-Path $OutputDir "$round-$variant"
 $arguments=@($Assets,$Modules,$InputFile,$Noise,"$prefix.f32",'--900','--wmma','--wave','--tiled','--pooled','--fused-c32','--fused-ffn','--fused-mh','--fast-mh','--mh-wave','--fast-deep','--fast-prefix','--skip-blocks','42,43,46','--repeat',"$Repeats")
 if($variant -eq 'packed'){$arguments+='--packed-weights'}
 $log=& $Runner @arguments 2>&1
 $status=$LASTEXITCODE
 $log | Set-Content "$prefix.log"
 if($status -ne 0){throw "Runner failed: $variant exit=$status"}
 $actual=(Get-FileHash "$prefix.f32" -Algorithm SHA256).Hash
 if($null -eq $hash){$hash=$actual}elseif($hash -ne $actual){throw "Numerical mismatch: $variant"}
 foreach($line in $log){if("$line" -match '^iteration=(\d+) wall_seconds=([\d.]+)'){$rows+=[pscustomobject]@{round=$round;variant=$variant;iteration=[int]$Matches[1];wall_ms=1000*[double]::Parse($Matches[2],[Globalization.CultureInfo]::InvariantCulture)}}}
 Write-Output "PASS round=$round variant=$variant sha256=$actual"
}
$rows | Export-Csv (Join-Path $OutputDir 'timings.csv') -NoTypeInformation
foreach($variant in @('baseline','packed')){
 $samples=@($rows | Where-Object {$_.variant -eq $variant -and $_.iteration -gt 0} | ForEach-Object {$_.wall_ms} | Sort-Object)
 $median=($samples[[int][Math]::Floor(($samples.Count-1)/2)]+$samples[[int][Math]::Floor($samples.Count/2)])/2
 Write-Output "RESULT variant=$variant samples=$($samples.Count) median_wall_ms=$median"
}

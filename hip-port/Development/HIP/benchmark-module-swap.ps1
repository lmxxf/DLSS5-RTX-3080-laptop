param([string]$Root='D:\DLSSNR-Lab\hip-backend',
 [string]$Module='c32_fused_ffn_attention.hsaco',
 [string]$Baseline='c32-base.hsaco',
 [string]$Candidate='c32-rtz.hsaco',
 [uint32]$Seed=0,
 [string]$HistoryFile='',
 [string]$Runner='reference_network.exe',
 [switch]$CandidatePackedC32,
 [switch]$BothPackedC32,
 [switch]$CandidateFp8Normalized,
 [switch]$BothFp8Normalized,
 [switch]$CandidateFp8Ffn,
 [switch]$CandidateFp8Av,
 [switch]$BothFp8Edges,
 [switch]$CandidateFp8Deep,
 [switch]$CandidateFp8Middle,
 [switch]$CandidateHalfC32,
 [switch]$BothCompactPipeline,
 [switch]$CandidateCropC32,
 [switch]$BothCropC32,
 [switch]$CandidateFusedQkvNorm,
 [switch]$BothFusedQkvNorm,
 [switch]$CandidateFusedMhFfn,
 [switch]$CandidateTiledMhFfn,
 [switch]$CandidateTiledMhFfnLarge,
 [switch]$BothSelectedMhFfn,
 [switch]$CandidateMappedC32,
 [switch]$BothMappedC32,
 [switch]$CandidateVitSplitK,
 [switch]$CandidateVitBlocked,
 [switch]$BothVitBlocked,
 [switch]$CandidateVitContractBlocked,
 [switch]$BothVitContractBlocked,
 [int]$CandidateVitWeightMask=0,
 [switch]$CandidateVitPackInput,
 [string]$BaselineModules='',
 [string]$CandidateModules='',
 [string]$Tag='module-swap-test',
 [string]$Assets='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets')
$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Close Stellar Blade before offline GPU timing.'}
$work=Join-Path $Root $Tag
New-Item -ItemType Directory -Force $work | Out-Null
$modules=Join-Path $work 'modules'
New-Item -ItemType Directory -Force $modules | Out-Null
Copy-Item "$Root\repro-modules\*.hsaco" $modules -Force
$rows=@();$expected=$null
foreach($round in 0..3){
 $variant=@('base','candidate','candidate','base')[$round]
  $source=if($variant -eq 'base'){$Baseline}else{$Candidate}
 if($BaselineModules -and $CandidateModules){
  $sourceDir=if($variant -eq 'base'){$BaselineModules}else{$CandidateModules}
  Copy-Item (Join-Path $sourceDir '*.hsaco') $modules -Force
 }else{Copy-Item (Join-Path $Root $source) (Join-Path $modules $Module) -Force}
 $output=Join-Path $work "$round-$variant.f32"
 $extra=@();if($HistoryFile){$extra+=@('--history',$HistoryFile)};if($BothPackedC32 -or ($CandidatePackedC32 -and $variant -eq 'candidate')){$extra+='--packed-c32'}
 if($BothFp8Normalized -or ($CandidateFp8Normalized -and $variant -eq 'candidate')){$extra+='--fp8-normalized'}
 if($BothFp8Edges){$extra+=@('--fp8-ffn','--fp8-av')}
 if($variant -eq 'candidate' -and $CandidateFp8Deep){$extra+='--fp8-deep'}
 if($variant -eq 'candidate'){if($CandidateFp8Ffn){$extra+='--fp8-ffn'};if($CandidateFp8Av){$extra+='--fp8-av'}}
 if($variant -eq 'candidate' -and $CandidateFp8Middle){$extra+='--fp8-middle'}
 if($variant -eq 'candidate' -and $CandidateHalfC32){$extra+='--half-c32'}
 if($BothCompactPipeline){$extra+=@('--fp8-deep','--fp8-middle','--half-c32')}
 if($variant -eq 'candidate' -and $CandidateCropC32){$extra+='--crop-c32'}
 if($BothCropC32){$extra+='--crop-c32'}
 if($BothFusedQkvNorm -or ($variant -eq 'candidate' -and $CandidateFusedQkvNorm)){$extra+='--fused-qkv-norm'}
 if($variant -eq 'candidate' -and $CandidateFusedMhFfn){$extra+='--fused-mh-ffn'}
 if($variant -eq 'candidate' -and $CandidateTiledMhFfn){$extra+='--tiled-mh-ffn'}
 if($variant -eq 'candidate' -and $CandidateTiledMhFfnLarge){$extra+='--tiled-mh-ffn-large'}
 if($BothSelectedMhFfn){$extra+=@('--fused-mh-ffn','--tiled-mh-ffn-large')}
 if($BothMappedC32 -or ($variant -eq 'candidate' -and $CandidateMappedC32)){$extra+='--mapped-c32'}
 if($variant -eq 'candidate' -and $CandidateVitSplitK){$extra+='--vit-split-k'}
 if($BothVitBlocked -or ($variant -eq 'candidate' -and $CandidateVitBlocked)){$extra+='--vit-blocked'}
 if($BothVitContractBlocked -or ($variant -eq 'candidate' -and $CandidateVitContractBlocked)){$extra+='--vit-contract-blocked'}
 if($variant -eq 'candidate' -and $CandidateVitWeightMask){$extra+=@('--vit-weight-mask',"$CandidateVitWeightMask")}
 if($variant -eq 'candidate' -and $CandidateVitPackInput){$extra+='--vit-pack-input'}
 $log=& (Join-Path $Root $Runner) $Assets $modules "$Root\input900.rgba32f" "$Assets\noise.f32" $output --900 --wmma --wave --tiled --pooled --fused-c32 --fused-ffn --fused-mh --fast-mh --mh-wave --fast-deep --fast-prefix --skip-blocks 42,43,46 --packed-weights --seed $Seed --repeat 6 @extra 2>&1
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started during benchmark; discard timing.'}
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
foreach($variant in @('base','candidate')){
 $hot=@($rows | Where-Object {$_.variant -eq $variant -and $_.iteration -gt 0} | ForEach-Object {$_.ms} | Sort-Object)
 Write-Output "RESULT variant=$variant median_ms=$(($hot[4]+$hot[5])/2)"
}

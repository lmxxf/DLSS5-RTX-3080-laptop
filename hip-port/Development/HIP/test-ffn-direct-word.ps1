# Isolated candidate; never modifies installed or release modules. Run after game/Magpie exit.
param([switch]$Timing)
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$lab='D:\DLSSNR-Lab'
function Closed {if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie first'}}
Closed
& "$lab\ffn-direct-src\test_fp8_staging.exe" "$lab\ffn-direct-src\fp8-staging-probe.hsaco"
if($LASTEXITCODE){throw 'FP8 roundtrip/staging failed'}
$baseline="$lab\dual-arch-modules\gfx1201";$candidate="$r\ffn-direct-word-modules"
New-Item -ItemType Directory -Force $candidate|Out-Null
Copy-Item "$baseline\*.hsaco" $candidate -Force
Copy-Item "$lab\ffn-direct-build\gfx1201\multihead-fast-padded-wave-packed.hsaco" $candidate -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0'
if($Timing){
 foreach($height in 900,1080){foreach($i in 0..3){
  Closed
  $m=if($i -in 1,2){$candidate}else{$baseline}
  & "$r\profile-1080.ps1" -Frames 80 -Tag "directword-$height-$i" -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $m -Runner benchmark_dual.exe -TimingOnly
 }}
 foreach($height in 900,1080){$hashes=@(foreach($i in 0..3){(Import-Csv "$r\profile1080\directword-$height-$i-summary.csv").hash});if(@($hashes|Select-Object -Unique).Count -ne 1){throw 'Timing output mismatch'}}
}else{
 # Add the same production flags to BOTH variants; generic harness otherwise uses the older 0.23 flags.
 $source=[IO.File]::ReadAllText("$r\validate-c32-register-ex.ps1")
 $needle='$f="$work\check-flags.txt";'
 if(!$source.Contains($needle)){throw 'Validation harness changed'}
 $source=$source.Replace($needle,('$flags+=@('''+$flags.Replace(';',"','")+''');'+$needle))
 $check="$lab\ffn-direct-src\validate-matched.ps1";[IO.File]::WriteAllText($check,$source)
 & $check -Candidate ffn-direct-word-modules -Baseline '..\dual-arch-modules\gfx1201' -Tag directword -Runner benchmark_dual.exe
 & $check -Extended -Candidate ffn-direct-word-modules -Baseline '..\dual-arch-modules\gfx1201' -Tag directword -Runner benchmark_dual.exe
}
Closed

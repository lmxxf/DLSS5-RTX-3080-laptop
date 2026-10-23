# Diagnostic ablation; zero noise intentionally changes the image. Never deploy these modules.
$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$r="$lab\hip-backend";$work="$r\profile1080"
$base="$lab\c256-frag-production-modules\gfx1201";$candidate="$r\prefix-noise-ablate-modules"
New-Item -ItemType Directory -Force $candidate|Out-Null;Copy-Item "$base\*.hsaco" $candidate -Force
Copy-Item "$lab\prefix-noise-ablate-build\gfx1201\c32_fused_ffn_attention-packed.hsaco" $candidate -Force
$flags='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1;DLSS5_HIP_MH_BYTE_STREAM=1;DLSS5_HIP_DECODER_BYTE=1;DLSS5_HIP_VIT_BYTE_STREAM=0;DLSS5_HIP_MH_FFN_FRAG256=1;DLSS5_HIP_GRAPH=0'
$expected=@{900='75AABA5EF94368353F3F17C034B53918151AA2EBC98FF870B2A057D08AE910AB';1080='1DE20C219105CC281CBA1364A0A21D0DDC4510A95458EC0CA3B8C893EA54F23A'}
$rows=@()
foreach($height in 900,1080){foreach($variant in 'base','zero-noise'){
 $m=if($variant -eq 'base'){$base}else{$candidate};$tag="prefix-noise-$height-$variant"
 & "$r\profile-1080.ps1" -Families 'none,c32prefix,none' -Frames 160 -WarmupFrames 32 -Tag $tag -ExtraFlag "$flags;DLSS5_NETWORK_HEIGHT=$height" -Modules $m -Runner benchmark_c256frag_production.exe -TimingOnly
 $v=@(Import-Csv "$work\$tag-summary.csv");if(@($v.hash|Select-Object -Unique).Count -ne 1){throw 'Duplication changed output within a variant'}
 if($variant -eq 'base' -and $v[0].hash -ne $expected[$height]){throw 'Baseline changed'}
 if($variant -eq 'zero-noise' -and $v[0].hash -eq $expected[$height]){throw 'Ablation did not change output'}
 $row=[pscustomobject]@{height=$height;variant=$variant;before_ms=[double]$v[0].median_ms;duplicate_ms=[double]$v[1].median_ms;after_ms=[double]$v[2].median_ms;prefix_marginal_ms=[double]$v[1].median_ms-([double]$v[0].median_ms+[double]$v[2].median_ms)/2;hash=$v[0].hash};$rows+=$row;$row|ConvertTo-Json -Compress
 $rows|Export-Csv "$work\prefix-noise-margins.csv" -NoTypeInformation
}}

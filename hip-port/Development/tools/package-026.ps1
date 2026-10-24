param([string]$ConfigDirectory=(Join-Path $PSScriptRoot '..\..\scripts'))
$ErrorActionPreference='Stop';$lab='D:\DLSSNR-Lab';$out='D:\給網友打包'
$addon="$lab\c256-frag-src\native-c256-fragment.addon64";$modules="$lab\c256-frag-production-modules"
$sha='f5d3f7348e42f362a0db4233814e1b2d8c4842de0d1196620a40bbc299adde75'
if((Get-FileHash $addon).Hash -ne $sha){throw 'Addon mismatch'}
$manifest=@(Get-Content "$lab\release-026-modules.sha256");if($manifest.Count -ne 48){throw 'Incomplete manifest'}
foreach($line in $manifest){if((Get-FileHash (Join-Path $modules $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Source kernel mismatch'}}
if((Get-FileHash "$lab\native_codec_decode.hlsl").Hash -ne '98a790d928e61c3eab905f43374dc9a1e560aff22946cd17b166cd0ca3e6c5f8'){throw 'Codec fix missing'}
foreach($name in 'Magpie-DLSS5-AMD-0.26','OptiScaler-DLSS5-AMD-0.26'){if((Test-Path "$out\$name") -or (Test-Path "$out\$name.zip")){throw "Output exists $name"}}
& "$lab\optiscaler-stellarblade.ps1" -Action Release -Version '0.26' -AddonPath $addon -AddonSha $sha -PreUpscale -ModulesPath $modules -Optimized -ConfigDirectory $ConfigDirectory
& "$lab\package-magpie-candidate.ps1" -Version '0.26' -Addon $addon -AddonSha $sha -Modules $modules -ConfigDirectory $ConfigDirectory
foreach($kind in 'OptiScaler','Magpie'){
 $stage="$out\$kind-DLSS5-AMD-0.26";$asset="$stage\DLSS5-AMD\native-game-tiled-assets"
 foreach($line in $manifest){if((Get-FileHash (Join-Path "$asset\HIP" $line.Substring(66))).Hash -ne $line.Substring(0,64)){throw 'Staged kernel mismatch'}}
 if((Get-FileHash "$stage\dlss5-amd.addon64").Hash -ne $sha){throw 'Staged addon mismatch'}
 if((Get-FileHash "$asset\native_codec_decode.hlsl").Hash -ne (Get-FileHash "$lab\native_codec_decode.hlsl").Hash){throw 'Stale decoder'}
 $flags=Get-Content "$stage\DLSS5-AMD\native-game-flags.txt"
 foreach($flag in 'DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1','DLSS5_HIP_MH_BYTE_STREAM=1','DLSS5_HIP_DECODER_BYTE=1','DLSS5_HIP_MH_FFN_FRAG256=1','DLSS5_HIP_VIT_BYTE_STREAM=0','DLSS5_NETWORK_HEIGHT=auto'){if($flags -notcontains $flag){throw "Missing flag $flag"}}
 $pre=if($kind -eq 'OptiScaler'){'DLSS5_PRE_UPSCALE=1'}else{'DLSS5_PRE_UPSCALE=0'};if($flags -notcontains $pre){throw 'Wrong integration path'}
 if(Test-Path "$asset\shader-cache"){throw 'Shader cache included'}
 if($kind -eq 'Magpie' -and !(Test-Path "$stage\Magpie.exe")){throw 'Not a complete Magpie bundle'}
 $hash=(Get-FileHash "$stage.zip").Hash.ToLowerInvariant();if(!(Get-Content "$stage.zip.sha256" -Raw).StartsWith($hash)){throw 'Zip checksum sidecar mismatch'}
 [pscustomobject]@{package="$kind-DLSS5-AMD-0.26.zip";bytes=(Get-Item "$stage.zip").Length;sha256=$hash;modules=48;addon=$sha;codec_fixed=$true}|ConvertTo-Json -Compress
}

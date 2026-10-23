# Uses an isolated header build that dumps raw bytes of blocks 5..22 and 47..65.
# Diagnostic only; timings are invalid. Verify final hashes against the non-dumping run.
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
$work="$r\profile1080\streamstage";New-Item -ItemType Directory -Force $work|Out-Null
foreach($variant in 'base','candidate'){
 $dir="$work\$variant";New-Item -ItemType Directory -Force $dir|Out-Null
 $flags=@(Get-Content "$a\native-game-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900','DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1',"DLSS5_DIAG_STAGE_DIR=$dir")
 $flags+=if($variant -eq 'base'){'DLSS5_HIP_MH_BYTE_STREAM=0'}else{'DLSS5_HIP_MH_BYTE_STREAM=1'}
 [IO.File]::WriteAllLines("$work\flags.txt",$flags)
 & "$r\benchmark_byte_stages.exe" "$a\native-game-tiled-assets" "$work\flags.txt" "$r\live-menu-before.f16" "$work\$variant-out" 1 0 "$r\mh-byte-stream-diag-modules" 0 0 123 0 > "$work\$variant.log"
 if($LASTEXITCODE){throw 'Stage diagnostic failed'}
 $reference="$r\profile1080\streamdiag-check-900-0-123-0-$variant-first.f16"
 if((Get-FileHash "$work\$variant-out.f16").Hash -ne (Get-FileHash $reference).Hash){throw 'Diagnostic changed final output; discard localization'}
 "$variant FINAL_MATCH"
}

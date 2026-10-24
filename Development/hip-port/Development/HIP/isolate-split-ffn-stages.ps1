$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
foreach($case in @('control','expand','contract')){
 & "$r\..\rtc_compile.exe" "$r\split-stage-$case.hsaco" "$r\split-stage-$case.hip" comgr
 if($LASTEXITCODE){throw 'Compile failed'}
 $m="$r\split-stage-$case-modules";New-Item -ItemType Directory -Force $m|Out-Null
 Copy-Item "$r\c256-attn-project-release-modules\*.hsaco" $m -Force
 Copy-Item "$r\split-stage-$case.hsaco" "$m\deep_fast-packed.hsaco" -Force
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
 & "$r\test_split_ffn_fp8.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" $m > "$r\split-stage-$case-test.log"
 $status=$LASTEXITCODE
 if($status -gt 1){throw 'Diagnostic failed before comparison'}
 Write-Output "CASE=$case EXIT=$status"
 Get-Content "$r\split-stage-$case-test.log" | Select-String 'bitdiff=[1-9]|invalid=[1-9]'
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_DUP_VIT_STAGE=|^DLSS5_DUP_BLOCKS='})
$base|Set-Content "$r\dupv-none-flags.txt"
foreach($s in 0..4){($base+@("DLSS5_DUP_VIT_STAGE=$s"))|Set-Content "$r\dupv-$s-flags.txt"}
$jobs=@('none','0','1','2','3','4','none')
$i=0;foreach($k in $jobs){
 Write-Output "ROUND=$k"
 & "$r\validate-hdr.ps1" -Runner benchmark_hlsl_vitdup.exe -Modules poolg-modules -Name "dupv-hlsl-$i-$k" -Flags "dupv-$k-flags.txt" -EdgesOnly 1 -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 $i++
}

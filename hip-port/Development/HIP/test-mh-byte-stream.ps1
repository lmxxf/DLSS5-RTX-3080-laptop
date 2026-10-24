$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-fp8-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_MH_BYTE_STREAM='})
($base+@('DLSS5_HIP_MH_BYTE_STREAM=0'))|Set-Content "$r\mh-byte-stream-off-flags.txt"
($base+@('DLSS5_HIP_MH_BYTE_STREAM=1'))|Set-Content "$r\mh-byte-stream-on-flags.txt"
& "$r\test_mh_byte_stream.exe" "$r\..\network-720p\DLSS5-AMD\native-game-tiled-assets" "$r\mh-byte-stream-modules"
if($LASTEXITCODE){throw 'byte stream mismatch'}
foreach($i in 0..3){
 $on=$i -in @(1,2)
 $modules=if($on){'mh-byte-stream-modules'}else{'vit-qkv-fp8-modules'}
 $flags=if($on){'mh-byte-stream-on-flags.txt'}else{'mh-byte-stream-off-flags.txt'}
 Write-Output "ROUND=$i modules=$modules flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_mh_byte_stream.exe -Modules $modules -Name "mh-byte-stream-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

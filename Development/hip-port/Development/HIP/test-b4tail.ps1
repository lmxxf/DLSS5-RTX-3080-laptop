$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_HIP_DOWN_CROP_FUSED=|^DLSS5_HIP_POOL32_H16W='})
($base+@('DLSS5_HIP_DOWN_CROP_FUSED=0','DLSS5_HIP_POOL32_H16W=0'))|Set-Content "$r\b4tail-off-flags.txt"
($base+@('DLSS5_HIP_DOWN_CROP_FUSED=1','DLSS5_HIP_POOL32_H16W=1'))|Set-Content "$r\b4tail-on-flags.txt"
foreach($i in 0..3){
 $flags=if($i -in @(1,2)){'b4tail-on-flags.txt'}else{'b4tail-off-flags.txt'}
 Write-Output "ROUND=$i flags=$flags"
 & "$r\validate-hdr.ps1" -Runner benchmark_b4tail.exe -Modules b4tail-modules -Name "b4tail-$i" -Flags $flags -EdgesOnly 1 -ExpectedHash FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

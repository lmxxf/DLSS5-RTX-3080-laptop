param([string]$Modules='c32h-modules',[string]$Runner='benchmark_vitcf.exe',[string]$FlagsBase='vitcf-on-flags.txt',[string]$Extra='DLSS5_HIP_PREFIX_INLINE=1',[string]$Tag='pinline2',[int]$CheckHash=1)
# ABBA on one module set: rounds 0/3 base flags, rounds 1/2 base flags + $Extra (one or more 'K=V' separated by ';').
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\$FlagsBase")
$keys=@($Extra.Split(';')|ForEach-Object{$_.Split('=')[0]})
$on=@($base|Where-Object{$k=$_.Split('=')[0];$keys -notcontains $k})+@($Extra.Split(';'))
$base|Set-Content "$r\$Tag-off-flags.txt";$on|Set-Content "$r\$Tag-on-flags.txt"
foreach($i in 0..3){
 $f=if($i -in @(1,2)){"$Tag-on-flags.txt"}else{"$Tag-off-flags.txt"}
 Write-Output "ROUND=$i flags=$f"
 & "$r\validate-hdr.ps1" -Runner $Runner -Modules $Modules -Name "$Tag-$i" -Flags $f -EdgesOnly 1 -ExpectedHash $(if($CheckHash){'FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58'}else{''})
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}

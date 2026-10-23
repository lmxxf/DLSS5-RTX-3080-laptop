param([string]$Runner='benchmark_hlsl_edges.exe',[string]$Tag='hlsl-cadence',[string]$ExpectedHash='C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$p=Start-Process "$r\read-adl-telemetry.exe" -ArgumentList '250' -RedirectStandardOutput "$r\$Tag-adl.log" -RedirectStandardError "$r\$Tag-adl-error.log" -PassThru -NoNewWindow
try{
 foreach($i in 0..3){
  if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
  $edges=@(0,1,1,0)[$i]
  Write-Output "BEGIN round=$i edges=$edges tick=$([Environment]::TickCount)"
  & "$r\validate-hdr.ps1" -Runner $Runner -Modules mh-input-mapped-release-modules -Name "$Tag-$i" -Flags rebind-async-flags.txt -EdgesOnly $edges -ExpectedHash $ExpectedHash
  Write-Output "END round=$i tick=$([Environment]::TickCount)"
  if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 }
}finally{$p.WaitForExit()}
if($p.ExitCode){throw 'Telemetry failed'}

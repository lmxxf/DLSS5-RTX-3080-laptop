$ErrorActionPreference='Stop'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$r='D:\DLSSNR-Lab\hip-backend'
$p=Start-Process "$r\read-adl-telemetry.exe" -ArgumentList '150' -RedirectStandardOutput "$r\hlsl-adl.log" -RedirectStandardError "$r\hlsl-adl-error.log" -PassThru -NoNewWindow
try{
 Write-Output "BEGIN_TICK=$([Environment]::TickCount)"
 & "$r\validate-hdr.ps1" -Runner benchmark_hlsl_lists.exe -Modules mh-input-mapped-release-modules -Name hlsl-adl-frame -Flags rebind-async-flags.txt -ExpectedHash C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B
 Write-Output "END_TICK=$([Environment]::TickCount)"
}finally{$p.WaitForExit()}
if($p.ExitCode){throw 'Telemetry failed'}
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started; discard measurements'}

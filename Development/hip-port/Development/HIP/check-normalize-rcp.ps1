$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
& "$r\..\rtc_compile.exe" "$r\test-normalize-rcp.hsaco" "$r\test-normalize-rcp.hip" comgr
if($LASTEXITCODE){throw 'Compile failed'}
& "$r\test-normalize-rcp.exe" "$r\test-normalize-rcp.hsaco"
if($LASTEXITCODE){throw 'Bounded reciprocal differs'}

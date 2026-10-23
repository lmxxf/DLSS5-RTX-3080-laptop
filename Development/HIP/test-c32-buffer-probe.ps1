$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\c32-buffer-src'
foreach($arch in 'gfx1200','gfx1201'){
 & 'D:\DLSSNR-Lab\dual-arch-src\rtc_compile.exe' "$r\c32-buffer-probe-$arch.hsaco" "$r\c32-buffer-probe.hip" comgr $arch
 if($LASTEXITCODE){throw 'Compile failed'}
}
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Exit game/Magpie'}
& "$r\test_buffer_half.exe" "$r\c32-buffer-probe-gfx1201.hsaco"
if($LASTEXITCODE){throw 'Probe failed'}

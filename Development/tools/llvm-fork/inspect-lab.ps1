$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\kernel-map'
Get-ChildItem $root -Filter '*.exe' | Select-Object Name,Length
Get-ChildItem "$root\production" -ErrorAction SilentlyContinue | Select-Object Name
Get-Process | Where-Object {$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile'} | Select-Object Id,ProcessName

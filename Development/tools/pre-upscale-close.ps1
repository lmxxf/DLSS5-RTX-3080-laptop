$ErrorActionPreference='Stop'
Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() } | Out-File D:\DLSSNR-Lab\pre-upscale\close-result.txt
Get-Process | Where-Object { $_.MainWindowTitle -eq 'Report Problem' } | ForEach-Object { $_.CloseMainWindow() } | Out-File D:\DLSSNR-Lab\pre-upscale\close-report-result.txt

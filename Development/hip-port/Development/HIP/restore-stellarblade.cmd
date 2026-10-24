@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy-stellarblade.ps1" -Action Restore
pause

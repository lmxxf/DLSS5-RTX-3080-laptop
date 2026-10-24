#!/bin/bash
# run-package-040.sh: one blocking wait (5 min steps) for no game + free gpu.lock, take it, run package-040.ps1 then verify040.ps1
# on the 9070 with a 15 s game watchdog, drop the lock. Logs: release-040\package.log / verify.log.
G='SB-Win64 StellarBlade Onimusha re9.exe SandFall LOP-Win64 Magpie Aniimo'
L='D:\DLSSNR-Lab\release-040'
while true; do
 out=$(ssh amd9070 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\DLSSNR-Lab\game-check.ps1 \"$G\" >nul && (echo GAME) || (if exist D:\DLSSNR-Lab\gpu.lock (echo BUSY) else (echo package-040 %DATE% %TIME% > D:\DLSSNR-Lab\gpu.lock & echo LOCKED))")
 [[ $out == *LOCKED* ]] && break
 timeout 300 tail -f /dev/null
done
echo "$(date +%T) lock taken"
ssh amd9070 "powershell -NoProfile -ExecutionPolicy Bypass -Command \"if('$1' -ne 'verify'){& '$L\package-040.ps1' -SourceCommit ${1:-3dc2f60b} *> '$L\package.log'; if(!\$?){exit 1}}; & '$L\verify040.ps1' *> '$L\verify.log'\"" & pid=$!
while kill -0 $pid 2>/dev/null; do
 if ssh amd9070 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\DLSSNR-Lab\game-check.ps1 \"$G\"" >/dev/null 2>&1; then echo GAME_ABORT; ssh amd9070 "taskkill /F /IM rt_bench.exe & taskkill /F /IM runtime-smoke.exe & taskkill /F /IM compile_fit_shaders.exe" >/dev/null 2>&1; break; fi
 timeout 15 tail -f /dev/null
done
wait $pid; rc=$?
ssh amd9070 "findstr package-040 D:\DLSSNR-Lab\gpu.lock >nul && del D:\DLSSNR-Lab\gpu.lock"; echo "DONE rc=$rc"

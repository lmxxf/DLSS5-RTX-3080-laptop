# game-check.ps1 <patterns...>  — shared "is a game running on the 9070" check (deployed at D:\DLSSNR-Lab\game-check.ps1).
# Drop-in for `tasklist | findstr /I "<patterns>"`: same exit code (0 = game running, 1 = none), patterns are
# space-separated case-insensitive substrings of the image name (e.g. "SB-Win64 Onimusha re9.exe").
# A matching process counts only if it has a main window, or started < 60 s ago (window not created yet).
# Windowless older matches are zombies (e.g. OnimushaWotS left behind after quitting): logged, not blocking.
# CAVEAT: over ssh (non-interactive session) MainWindowHandle is ALWAYS 0, even for a real game on the desktop.
# So a windowless match still counts as live if it holds >= 200 MB dedicated GPU memory (counters are visible from
# ssh; the zombie holds none). Only queried when an old windowless match exists.
$pats = @($args | ForEach-Object { "$_" -split '\s+' } | Where-Object { $_ })
if (-not $pats) { Write-Output 'usage: game-check.ps1 <patterns...>'; exit 2 }
$log = Join-Path $PSScriptRoot 'game-check.log'
$now = Get-Date; $live = $false; $gpu = $null
foreach ($p in Get-Process -ErrorAction SilentlyContinue) {
  $img = "$($p.ProcessName).exe"
  if (-not ($pats | Where-Object { $img.IndexOf($_, [StringComparison]::OrdinalIgnoreCase) -ge 0 })) { continue }
  $young = $false; try { $young = ($now - $p.StartTime).TotalSeconds -lt 60 } catch {}
  if ($p.MainWindowHandle -ne 0 -or $young) { Write-Output "GAME $img pid $($p.Id)"; $live = $true }
  else {
    if ($null -eq $gpu) { $gpu = @{}; try { (Get-Counter '\GPU Process Memory(*)\Dedicated Usage' -MaxSamples 1 -ErrorAction Stop).CounterSamples |
      ForEach-Object { if ($_.InstanceName -match 'pid_(\d+)_') { $gpu[[int]$matches[1]] += $_.CookedValue } } } catch {} }
    if ($gpu[$p.Id] -ge 200MB) { Write-Output "GAME $img pid $($p.Id) (no window visible, gpu $([int]($gpu[$p.Id]/1MB)) MB)"; $live = $true; continue }
    $m = "zombie game process ignored: $img pid $($p.Id)"
    Write-Output $m
    try { Add-Content -Path $log -Value "$($now.ToString('s')) $m" } catch {}
  }
}
if ($live) { exit 0 } else { exit 1 }

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
@(Get-Process | Where-Object { $_.ProcessName -match 'Onimusha|StellarBlade|Magpie' } | Select-Object ProcessName,Id,Path) | ConvertTo-Json -Depth 3
